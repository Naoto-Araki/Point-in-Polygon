# PLATEAUの属性情報において，建築年が2010年以降(2010年は含まない)の建物を除く
import geopandas as gpd
import pandas as pd

# .shp ファイルのパス
shp_file_path = "PLATEAU/博多区PLATEAU.shp"
filtered_shp_path = "PLATEAU/博多区PLATEAU_除外.shp"

# .shp ファイルを読み込む
gdf = gpd.read_file(shp_file_path)

# 建築年の列を確認
print("Available columns:", gdf.columns)

gdf["Year"] = pd.to_numeric(gdf["Year"], errors="coerce")

# 建築年が2010年以前のデータのみを抽出
if "Year" in gdf.columns:
    gdf_filtered = gdf[gdf["Year"] <= 2010]

    # フィルタリング結果を保存
    gdf_filtered.to_file(filtered_shp_path, driver="ESRI Shapefile")
    print(f"Filtered Shapefile has been saved to: {filtered_shp_path}")
else:
    print("The column 'Year' does not exist in the dataset.")
