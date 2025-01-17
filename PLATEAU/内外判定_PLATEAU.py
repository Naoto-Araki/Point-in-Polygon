import geopandas as gpd

# 町丁目境界線のShapefile
towns_shp_path = "博多区町丁目境界線ポリゴン.shp"
towns_gdf = gpd.read_file(towns_shp_path)

# PLATEAU建物ポリゴンのShapefile
buildings_shp_path = "PLATEAU/博多区PLATEAU.shp"
buildings_gdf = gpd.read_file(buildings_shp_path)

# buildings_shp_path = "PLATEAU/博多区PLATEAU_除外.shp"
# buildings_gdf = gpd.read_file(buildings_shp_path)

# 列名の確認
print("建物ポリゴンの列名:")
print(buildings_gdf.columns)

# データのサンプルを表示
print("\nデータサンプル:")
print(buildings_gdf.head())

# CRSを統一し、平面座標系に変換
crs_projected = "EPSG:6668"  # 平面座標系 (JGD2011)
if buildings_gdf.crs != crs_projected:
    buildings_gdf = buildings_gdf.to_crs(crs_projected)
if towns_gdf.crs != crs_projected:
    towns_gdf = towns_gdf.to_crs(crs_projected)

# 町丁目の識別列（Name）と建物の識別列（BuildingID）の確認
if "BuildingID" not in buildings_gdf.columns:
    raise ValueError("建物ポリゴンに 'BuildingID' 列がありません。")
if "Name" not in towns_gdf.columns:
    raise ValueError("町丁目データに 'Name' 列がありません。")

# 1. 建物ポリゴンと町丁目の交差部分を計算
intersection_gdf = gpd.overlay(buildings_gdf, towns_gdf, how="intersection")

# 2. 交差部分の面積を計算
intersection_gdf["area"] = intersection_gdf.geometry.area

# 3. 各建物の BuildingID ごとに最大面積を持つ町丁目を選択
max_area_gdf = intersection_gdf.loc[intersection_gdf.groupby("BuildingID")["area"].idxmax()]

# 4. 元の建物データに最大面積の町丁目情報（Name列）を統合
result_gdf = buildings_gdf.merge(
    max_area_gdf[["BuildingID", "Name"]], on="BuildingID", how="left"
)

# 結果の保存
output_path = "博多区PLATEAU_町丁目付加.shp"
result_gdf.to_file(output_path)

print(f"結果を保存しました: {output_path}")