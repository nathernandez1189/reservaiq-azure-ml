# CSV listo para cargar

Selecciona reservas-listas.csv en «Explorar una reserva → Analizar un lote de reservas» y pulsa «Analizar lote». Contiene ocho reservas históricas de la partición de prueba, sin resultado de cancelación ni identificadores personales. Mantén la extensión .csv y el separador coma.

| Variable | Significado | Valores admitidos |
| --- | --- | --- |
| lead_time | Días de anticipación | Entero 0–60 |
| arrival_month | Mes de llegada | Entero 1–12 |
| stays_in_weekend_nights | Noches de fin de semana | Entero 0–15 |
| stays_in_week_nights | Noches entre semana | Entero 0–30 |
| hotel | Tipo de hotel | City Hotel, Resort Hotel |
| meal | Alimentación | BB, HB, FB, SC, Undefined |
| market_segment | Segmento | Direct, Corporate, Online TA, Offline TA/TO, Complementary, Groups, Aviation |
| distribution_channel | Canal | Direct, Corporate, TA/TO, GDS |
| reserved_room_type | Habitación reservada | A, B, C, D, E, F, G, H, L, P |
| customer_type | Tipo de reserva | Transient, Transient-Party, Contract, Group |

La suma de noches debe estar entre 1 y 30. La aplicación admite entre 1 y 500 filas, máximo 150 KB. No agregues títulos, columnas ni celdas vacías al CSV. Si lo editas en Excel, guárdalo como CSV UTF-8 delimitado por comas.

Fuente: Antonio, Almeida y Nunes (2019), https://doi.org/10.1016/j.dib.2018.11.126. Distribución TidyTuesday, https://github.com/rfordatascience/tidytuesday/tree/main/data/2020/2020-02-11. Datos originales CC BY 4.0. El mes numérico y la selección de filas se derivaron para este proyecto.
