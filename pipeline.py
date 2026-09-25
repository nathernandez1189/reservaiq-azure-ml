"""Reproducible local/Azure ML stages: prepare, train and evaluate."""
import argparse,hashlib,json,platform,time
from pathlib import Path
import joblib,numpy as np,pandas as pd,sklearn
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier,HistGradientBoostingClassifier
from sklearn.dummy import DummyClassifier
from sklearn.metrics import average_precision_score,roc_auc_score,precision_score,recall_score,f1_score,confusion_matrix,brier_score_loss
from sklearn.inspection import permutation_importance
from core import FEATURES,NUMERIC,CATEGORICAL,CATEGORIES

SEED=42
def write(path,data):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
def metrics(y,p,t):
    pred=p>=t;tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel()
    k=max(1,int(np.ceil(len(y)*.2)));ix=np.argsort(-p,kind='stable')[:k];positives=int(sum(y));hits=int(np.asarray(y)[ix].sum())
    return {'average_precision':float(average_precision_score(y,p)), 'roc_auc':float(roc_auc_score(y,p)),
      'precision':float(precision_score(y,pred,zero_division=0)), 'recall':float(recall_score(y,pred,zero_division=0)),
      'f1':float(f1_score(y,pred,zero_division=0)),'brier':float(brier_score_loss(y,p)),
      'tn':int(tn),'fp':int(fp),'fn':int(fn),'tp':int(tp),'threshold':float(t),'n':len(y),'positives':positives,
      'top20':{'k':k,'hits':hits,'precision':hits/k,'recall':hits/positives,'lift':(hits/k)/(positives/len(y))}}

def prepare(source,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    raw=pd.read_csv(source,keep_default_na=False);assert len(raw)==119390
    raw['row_id']=np.arange(len(raw))+1
    months={m:i+1 for i,m in enumerate(['January','February','March','April','May','June','July','August','September','October','November','December'])}
    raw['arrival_month']=raw.arrival_date_month.map(months)
    raw['arrival']=pd.to_datetime(dict(year=raw.arrival_date_year,month=raw.arrival_month,day=raw.arrival_date_day_of_month))
    raw['booking']=raw.arrival-pd.to_timedelta(raw.lead_time,unit='D')
    raw['resolved']=pd.to_datetime(raw.reservation_status_date)
    nights=raw.stays_in_weekend_nights+raw.stays_in_week_nights
    scope=(raw.lead_time.between(0,60)&nights.between(1,30)&raw.stays_in_weekend_nights.between(0,15))
    for c in CATEGORICAL:scope &= raw[c].isin(CATEGORIES[c])
    scoped=raw[scope].copy().rename(columns={'is_canceled':'target'})
    # Exact duplicate exports can overweight group patterns. Keep first exact row;
    # retain distinct records with same predictors when outcomes/other data differ.
    before=len(scoped);dupcols=[c for c in raw.columns if c not in ['row_id']]
    dupcols=['target' if c=='is_canceled' else c for c in dupcols]
    scoped=scoped.drop_duplicates(subset=dupcols)
    spans=[('train','2015-07-01','2016-07-01','2016-09-01'),('validation','2016-09-01','2016-12-01','2017-02-01'),('test','2017-02-01','2017-06-01','2017-09-01')]
    sizes={};used=[]
    for name,start,end,known in spans:
        part=scoped[(scoped.booking>=start)&(scoped.booking<end)&(scoped.resolved<known)].sort_values(['booking','row_id'])
        cols=['row_id','booking','arrival','resolved']+FEATURES+['target']
        part[cols].to_csv(out/f'{name}.csv',index=False);used.extend(part.row_id.tolist())
        sizes[name]={'n':len(part),'positives':int(part.target.sum()),'prevalence':float(part.target.mean()),'booking_start':start,'booking_end_exclusive':end,'outcome_known_before':known}
    assert len(used)==len(set(used)) and all(x['positives']>0 for x in sizes.values())
    exclusions=[c for c in raw.columns if c not in FEATURES+['row_id','arrival_month']]
    write(out/'data_manifest.json',{'source':'https://doi.org/10.1016/j.dib.2018.11.126','download':'https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2020/2020-02-11/hotels.csv','license':'CC BY 4.0','synthetic':False,'raw_rows':len(raw),'scope_rows_before_dedup':before,'exact_duplicates_removed':before-len(scoped),'scope_rows_after_dedup':len(scoped),'used_rows':len(used),'scope_rows_outside_splits_or_maturity':len(scoped)-len(used),'features':FEATURES,'excluded':exclusions,'sha256':hashlib.sha256(Path(source).read_bytes()).hexdigest(),'splits':sizes,'scope':'Lead time 0–60 days; total stay 1–30 nights; known categorical values. Two hotels in Portugal.','split_method':'Derived booking date with gaps between train/validation/test; outcomes must be resolved before next evaluation period. Retrospective data are not a versioned snapshot of booking-time fields.','limitations':['Arrival-limited historical sample from two hotels; not a representative market sample.','Derived booking date assumes recorded lead_time and arrival date reflect initial booking.','Exact-row duplicates removed; indistinguishable legitimate bookings may also be removed.','No guest identifier: recurrent-guest or group dependence cannot be fully excluded.']})
    print('Particiones:',sizes,flush=True)

def train(data,out):
    data,out=Path(data),Path(out);out.mkdir(parents=True,exist_ok=True)
    tr=pd.read_csv(data/'train.csv',keep_default_na=False);va=pd.read_csv(data/'validation.csv',keep_default_na=False)
    estimators={'Base de referencia':DummyClassifier(strategy='prior'),
      'Regresión logística':LogisticRegression(max_iter=1500,random_state=SEED),
      'Random Forest':RandomForestClassifier(n_estimators=160,min_samples_leaf=12,max_features=.8,random_state=SEED,n_jobs=2),
      'Gradient Boosting':HistGradientBoostingClassifier(max_iter=160,max_leaf_nodes=15,l2_regularization=5,learning_rate=.06,random_state=SEED)}
    scores=[];models={}
    for name,estimator in estimators.items():
        prep=ColumnTransformer([('num',StandardScaler(),NUMERIC),('cat',OneHotEncoder(handle_unknown='ignore',sparse_output=False),CATEGORICAL)])
        model=Pipeline([('prepare',prep),('classifier',estimator)]);start=time.time()
        model.fit(tr[FEATURES],tr.target);p=model.predict_proba(va[FEATURES])[:,1]
        score=metrics(va.target,p,.5);score.update(name=name,training_seconds=round(time.time()-start,2));scores.append(score);models[name]=model
        print(name,'AP validación',round(score['average_precision'],4),flush=True)
    best=max([s for s in scores if s['name']!='Base de referencia'],key=lambda s:s['average_precision']);model=models[best['name']]
    p=model.predict_proba(va[FEATURES])[:,1];sweep=[metrics(va.target,p,t) for t in np.arange(.05,.951,.01)]
    chosen=max(sweep,key=lambda x:(x['f1'],x['precision']))
    bundle={'model':model,'name':best['name'],'threshold':chosen['threshold'],'version':'reservaiq-1.0','seed':SEED}
    joblib.dump(bundle,out/'model.joblib',compress=3)
    write(out/'selection.json',{'candidates':scores,'selected':best['name'],'criterion':'Maximum validation average precision','threshold_criterion':'Maximum validation F1 on prespecified grid 0.05–0.95. Test never used for selection.','validation':chosen,'threshold_sweep':sweep,'seed':SEED,'python':platform.python_version(),'sklearn':sklearn.__version__,'numpy':np.__version__,'pandas':pd.__version__})
    va.assign(score=p).to_csv(out/'validation_predictions.csv',index=False)
    print('Selección:',best['name'],'umbral',chosen['threshold'],flush=True)

def evaluate(data,trained,out):
    data,trained,out=Path(data),Path(trained),Path(out);out.mkdir(parents=True,exist_ok=True)
    bundle=joblib.load(trained/'model.joblib');selection=json.loads((trained/'selection.json').read_text());manifest=json.loads((data/'data_manifest.json').read_text())
    te=pd.read_csv(data/'test.csv',keep_default_na=False);va=pd.read_csv(data/'validation.csv',keep_default_na=False)
    y=te.target.to_numpy();p=bundle['model'].predict_proba(te[FEATURES])[:,1];m=metrics(y,p,bundle['threshold'])
    n=m['positives'];r=m['recall'];z=1.96;den=1+z*z/n;center=(r+z*z/(2*n))/den;half=z*np.sqrt(r*(1-r)/n+z*z/(4*n*n))/den;m['recall_wilson_95']=[float(center-half),float(center+half)]
    sample=va.sample(min(2500,len(va)),random_state=SEED)
    imp=permutation_importance(bundle['model'],sample[FEATURES],sample.target,scoring='average_precision',n_repeats=3,random_state=SEED,n_jobs=1)
    importance=sorted([{'feature':f,'mean':float(v),'std':float(s)} for f,v,s in zip(FEATURES,imp.importances_mean,imp.importances_std)],key=lambda a:a['mean'],reverse=True)
    scored=te.assign(score=p,flagged=(p>=bundle['threshold']).astype(int));scored.to_csv(out/'test_predictions.csv',index=False)
    examples=[]
    for label,mask in [('Cancelación detectada',(y==1)&(p>=bundle['threshold'])),('Seguimiento habitual',(y==0)&(p<bundle['threshold'])),('Falsa alerta',(y==0)&(p>=bundle['threshold'])),('Cancelación omitida',(y==1)&(p<bundle['threshold']))]:
        group=scored[mask].sort_values('score')
        if len(group):
            row=group.iloc[len(group)//2];examples.append({'label':label,'row_id':int(row.row_id),'actual':int(row.target),'score':float(row.score),'inputs':{f:int(row[f]) if f in NUMERIC else str(row[f]) for f in FEATURES}})
    # A real fixed holdout cohort used to illustrate a capacity-constrained queue.
    cohort=scored.tail(150).sort_values('score',ascending=False)
    queue=[{'id':f'R-{int(row.row_id):06d}','hotel':row.hotel,'lead_time':int(row.lead_time),'nights':int(row.stays_in_weekend_nights+row.stays_in_week_nights),'segment':row.market_segment,'booking':row.booking,'score':float(row.score),'actual':int(row.target),'inputs':{f:int(row[f]) if f in NUMERIC else str(row[f]) for f in FEATURES}} for row in cohort.itertuples(index=False) for row in [pd.Series(row._asdict())]]
    monthly=[]
    for period,g in scored.groupby(scored.booking.str[:7]):
        monthly.append({'month':period,'n':len(g),'cancellations':int(g.target.sum()),'flagged':int(g.flagged.sum()),'mean_score':float(g.score.mean())})
    by_hotel=[]
    for hotel,g in scored.groupby('hotel'):
        by_hotel.append({'hotel':hotel,**metrics(g.target,g.score,bundle['threshold'])})
    summary={'project':'ReservaIQ','local_verified':True,'azure_verified':False,'model':bundle['name'],'version':bundle['version'],'threshold':bundle['threshold'],'data':manifest,'selection':selection,'test':m,'importance_validation':importance,'importance_sample_n':len(sample),'examples':examples,'queue':queue,'monthly':monthly,'by_hotel':by_hotel,'limitations':['Datos de dos hoteles de Portugal en 2015–2017; cliente del proyecto ficticio.','Evaluación retrospectiva: no hay versiones de cada variable al momento de reservar.','Índice del clasificador no calibrado; no equivale a certeza.','No se demuestra que una llamada evite una cancelación.','No se cancela, cobra, discrimina ni modifica ninguna reserva.']}
    write(out/'summary.json',summary)
    te[FEATURES].head(8).to_csv(out/'demo-input.csv',index=False)
    print('Prueba reservada:',json.dumps(m,ensure_ascii=False),flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('stage',choices=['prepare','train','evaluate','all']);a.add_argument('--data',default='data/hotels.csv');a.add_argument('--splits',default='artifacts/splits');a.add_argument('--trained',default='artifacts/trained');a.add_argument('--out',default='artifacts');v=a.parse_args()
    if v.stage in ['prepare','all']:prepare(v.data,v.splits)
    if v.stage in ['train','all']:train(v.splits,v.trained)
    if v.stage in ['evaluate','all']:evaluate(v.splits,v.trained,v.out)
