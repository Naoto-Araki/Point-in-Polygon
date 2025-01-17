import geopandas as gpd
import os

# ファイルパス
buildings_shp_path = "PLATEAU/博多区PLATEAU_除外_町丁目付加.shp"  # 町丁目情報が付加された建物ポリゴン
output_dir = "PLATEAU/町丁目_除外後"  # 出力先のディレクトリ

# Shapefile を読み込む
buildings_gdf = gpd.read_file(buildings_shp_path)

# 町丁目情報の列名（適宜変更）
town_column = "Name"  # 町丁目を識別する列名

# 町丁目ごとにデータを分割して保存
for town_name, group in buildings_gdf.groupby(town_column):
    # 出力ファイル名を作成
    output_path = os.path.join(output_dir, f"{town_name}.shp")

    # データを保存
    group.to_file(output_path, driver="ESRI Shapefile")

    print(f"Saved: {output_path}")
