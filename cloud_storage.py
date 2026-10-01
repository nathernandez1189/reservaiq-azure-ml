"""Bounded academic demo: in-memory SQLite transactions, atomic Blob snapshots.

SQLite never opens a database on a mounted network filesystem. Each request reads
the private snapshot; successful writes replace it conditionally with its ETag.
The local application's SQLite file and historical model files are not uploaded.
"""
from contextlib import contextmanager
import sqlite3
from storage import ReservationStore, ConflictError

MAX_SNAPSHOT_BYTES = 16 * 1024 * 1024


class BlobReservationStore(ReservationStore):
    kind = 'azure_blob'

    def __init__(self, transport):
        self.transport = transport

    @contextmanager
    def connect(self):
        data, etag = self.transport.read()
        if data is not None and len(data) > MAX_SNAPSHOT_BYTES:
            raise OSError('La copia supera el límite de esta demo.')
        con = sqlite3.connect(':memory:', timeout=10)
        try:
            if data is not None:
                con.deserialize(data)
            self.initialize(con)
            before = con.total_changes
            with con:
                yield con
            if con.total_changes != before:
                image = con.serialize()
                if len(image) > MAX_SNAPSHOT_BYTES:
                    raise OSError('La copia supera el límite de esta demo.')
                self.transport.write(image, etag)
        finally:
            con.close()

    def check(self):
        with self.connect() as con:
            con.execute('SELECT 1').fetchone()


class AzureBlobTransport:
    """Use only the App Service managed identity, never account keys or SAS."""
    def __init__(self, account_url, container, blob='reservas.sqlite3'):
        from urllib.parse import urlparse
        from azure.identity import ManagedIdentityCredential
        from azure.storage.blob import BlobClient
        u = urlparse(account_url)
        if (u.scheme != 'https' or not u.hostname or not u.hostname.endswith('.blob.core.windows.net')
                or u.username or u.password or u.query or u.fragment or u.path not in ('', '/')):
            raise ValueError('La cuenta de almacenamiento no es válida.')
        self.client = BlobClient(account_url=account_url, container_name=container,
                                 blob_name=blob, credential=ManagedIdentityCredential(),
                                 retry_total=2, connection_timeout=5, read_timeout=20)

    def read(self):
        from azure.core.exceptions import AzureError, ResourceNotFoundError
        try:
            stream = self.client.download_blob(max_concurrency=1)
            if stream.size > MAX_SNAPSHOT_BYTES:
                raise OSError('La copia supera el límite de esta demo.')
            return stream.readall(), stream.properties.etag
        except ResourceNotFoundError as error:
            if error.error_code == 'BlobNotFound':
                return None, None
            raise OSError('El almacenamiento de la demo no está disponible.') from None
        except AzureError:
            raise OSError('No se pudo consultar el almacenamiento de Azure.') from None

    def write(self, image, etag):
        from azure.core import MatchConditions
        from azure.core.exceptions import AzureError, ResourceExistsError, ResourceModifiedError
        try:
            if etag is None:
                self.client.upload_blob(image, overwrite=False)
            else:
                self.client.upload_blob(image, overwrite=True, etag=etag,
                                        match_condition=MatchConditions.IfNotModified)
        except (ResourceExistsError, ResourceModifiedError):
            raise ConflictError('Otra ventana guardó un cambio. Actualiza Mis reservas y vuelve a intentar; no se sobrescribieron datos.') from None
        except AzureError:
            raise OSError('No se pudo guardar en Azure. Conserva este intento y vuelve a probar.') from None
