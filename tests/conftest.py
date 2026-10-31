import pytest
from ine_perfiles import config as C


@pytest.fixture(scope="session")
def con():
    if not any(C.INTERIM_CCPC.glob("aelec=*/*.parquet")):
        pytest.skip("Parquet no generado: corre scripts/datos/ingesta_ccpc.py")
    from ine_perfiles.ingesta import conectar
    return conectar()
