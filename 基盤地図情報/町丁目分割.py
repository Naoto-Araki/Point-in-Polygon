import geopandas as gpd
import os

# ファイルパス
buildings_shp_path = "博多区建物ポリゴン_2010_町丁目付加.shp"  # 町丁目情報が付加された建物ポリゴン
output_dir = "基盤地図情報"  # 出力先のディレクトリ

# Shapefile を読み込む
buildings_gdf = gpd.read_file(buildings_shp_path)

# 町丁目情報の列名（適宜変更）
town_column = "Name_1"  # 町丁目を識別する列名

# 町丁目ごとにデータを分割して保存
for town_name, group in buildings_gdf.groupby(town_column):
    # 出力ファイル名を作成
    output_path = os.path.join(output_dir, f"{town_name}.shp")

    # データを保存
    group.to_file(output_path, driver="ESRI Shapefile")

    print(f"Saved: {output_path}")
