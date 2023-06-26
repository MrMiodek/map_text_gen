# MAP_TEXT_GEN

Early version of library allowing user to download OSM data, divide it into tiles, store it in GeoDataframe, enrich it with usefull columns and transform it to LLM token efficient format.



## Instalation

This tool works only on Ubuntu\WSL
Before other libraries please install tippecanoe (placed in default location '/usr/local/bin/') and togeojson
Both are needed to use togeojson library  (see https://pypi.org/project/togeojsontiles/ )

To install other dependencies run:

```
pip install -r requirements.txt
```

## Usage

Example usage is shown in [Demo16](Demo16.ipynb) and [Demo18](Demo18.ipynb). These are identical files (the only difference is data zoom) that show example usage of available functions.
