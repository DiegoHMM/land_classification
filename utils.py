# src/utils.py

import geopandas as gpd
from pystac_client import Client
import odc.stac
import ast
import rioxarray
import logging
import os
import json
from pathlib import Path

logger = logging.getLogger(__name__)

def create_bbox_list_from_shapefile(shapefile_path, buffer_size=0.001):
    """
    Lê um shapefile de grid, calcula o centroide de cada célula e cria
    uma bounding box (bbox) ao redor de cada centroide.

    Args:
        shapefile_path (str): O caminho para o arquivo .shp do grid.
        buffer_size (float): O tamanho do buffer para criar a bbox ao redor do centroide.

    Returns:
        list: Uma lista de tuplas, onde cada tupla contém (cell_id, bbox_string).
              Retorna uma lista vazia se o arquivo não for encontrado.
    """
    try:
        grid = gpd.read_file(shapefile_path)
        grid_wgs84 = grid.to_crs(epsg=4326)
        bbox_list = []

        for _, cell in grid_wgs84.iterrows():
            cell_id = cell['NOARQXWD'] if 'NOARQXWD' in cell else cell.name
            centroid = cell.geometry.centroid
            
            minx = centroid.x - buffer_size
            maxx = centroid.x + buffer_size
            miny = centroid.y - buffer_size
            maxy = centroid.y + buffer_size
            
            bbox_str = f"[{minx}, {miny}, {maxx}, {maxy}]"
            bbox_list.append((cell_id, bbox_str))
            
        logger.info(f"{len(bbox_list)} bboxes geradas a partir de {shapefile_path}")
        return bbox_list

    except FileNotFoundError:
        logger.error(f"Arquivo de grid '{shapefile_path}' não encontrado.")
        return []

def load_checkpoint(checkpoint_file):
    """Carrega o estado do checkpoint se o arquivo existir."""
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r') as f:
            logger.info(f"Checkpoint encontrado em '{checkpoint_file}'. Carregando estado.")
            return json.load(f)
    logger.info("Nenhum checkpoint encontrado. Iniciando do zero.")
    return {'completed': [], 'failed': []}

def save_checkpoint(checkpoint_file, state):
    """Salva o estado atual no arquivo de checkpoint."""
    with open(checkpoint_file, 'w') as f:
        json.dump(state, f, indent=4)
    logger.debug(f"Checkpoint salvo em '{checkpoint_file}'.")

def get_datacube(catalog_url, bbox, product_name, time_interval, resolution, bands, crs):
    """
    Busca e carrega um cubo de dados de um catálogo STAC.
    """
    try:
        client = Client.open(catalog_url, timeout=60)
        search = client.search(
            collections=[product_name],
            bbox=ast.literal_eval(bbox),
            datetime=time_interval,
        )
        items = search.item_collection()
        
        if not items:
            logger.warning(f"Nenhum item encontrado para {product_name} no bbox {bbox} e intervalo {time_interval}")
            return None
        
        for item in items:
            for asset in item.assets.values():
                if "proj:epsg" not in asset.extra_fields and "proj:code" in asset.extra_fields:
                    asset.extra_fields["proj:epsg"] = int(asset.extra_fields["proj:code"].split(":")[1])
        
        return odc.stac.load(
            items,
            bands=bands,
            crs=crs,
            resolution=resolution,
        )
    except Exception as e:
        logger.error(f"Erro ao buscar dados de {product_name} no bbox {bbox}: {e}")
        return None

def process_and_save_datacube(datacube, output_file):
    """
    Processa um datacubo xarray e o salva como um GeoTIFF.
    
    Args:
        datacube (xarray.Dataset): O datacubo a ser processado.
        output_file (str): Caminho do arquivo de saída .tif.
        
    Returns:
        bool: True se o salvamento foi bem-sucedido, False caso contrário.
    """
    if datacube is not None and len(datacube.time) > 0:
        data_array = datacube.isel(time=0).to_array('band').transpose('band', 'y', 'x')
        data_array.rio.to_raster(output_file, driver="GTiff")
        logger.info(f"Dados salvos em {output_file}")
        return True
    else:
        logger.warning(f"Datacubo vazio ou inválido. Não foi possível salvar em {output_file}.")
        return False