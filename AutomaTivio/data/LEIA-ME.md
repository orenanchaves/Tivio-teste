# data/

`tivio_summary.json`: o JSON do Informativo Tivio (`/api/home/summary`),
exportado com o login corporativo e salvo aqui. Dele saem os AUMs por vertical
de todos os materiais (`datasources/aum_verticais.py`).

**É dado interno e não vai para o GitHub** (está no `.gitignore`). Atualize o
arquivo antes de rodar o mês; sem ele, `python run.py` para e avisa.
