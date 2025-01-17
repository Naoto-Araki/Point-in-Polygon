import os
import geopandas as gpd
import pandas as pd

def exact_match(kiban_gdf, plateau_gdf):
    """
    完全一致 (equals) 判定を行う関数。

    Args:
        kiban_gdf (GeoDataFrame): 基盤地図情報の建物ポリゴン
        plateau_gdf (GeoDataFrame): プラトーの建物ポリゴン

    Returns:
        GeoDataFrame: 一致するポリゴンの情報
    """
    matches = []
    for _, kiban_row in kiban_gdf.iterrows():
        for _, plateau_row in plateau_gdf.iterrows():
            if kiban_row.geometry.equals(plateau_row.geometry):
                matches.append({
                    "kiban_id": kiban_row["gml_id"],
                    "plateau_id": plateau_row["BuildingID"],
                    "geometry": kiban_row.geometry
                })
    
    # matches が空の場合の処理
    if not matches:
        return gpd.GeoDataFrame(columns=["kiban_id", "plateau_id", "geometry"], crs=kiban_gdf.crs)
    
    # GeoDataFrame として返す
    return gpd.GeoDataFrame(matches, crs=kiban_gdf.crs, geometry="geometry")



def significant_overlap(kiban_gdf, plateau_gdf, threshold=0.7):
    """
    両方の重なり率を考慮した一致判定を行う関数。

    Args:
        kiban_gdf (GeoDataFrame): 基盤地図情報の建物ポリゴン。
        plateau_gdf (GeoDataFrame): プラトーの建物ポリゴン。
        threshold (float): 重なり面積の割合の閾値（0～1）。

    Returns:
        GeoDataFrame: 両方の重なり率が閾値以上の一致結果。
    """
    # 交差計算
    intersection = gpd.overlay(kiban_gdf, plateau_gdf, how="intersection")

    # 面積計算
    intersection["intersection_area"] = intersection.geometry.area
    kiban_areas = kiban_gdf.set_index("gml_id").geometry.area
    plateau_areas = plateau_gdf.set_index("BuildingID").geometry.area

    intersection["kiban_area"] = intersection["gml_id"].map(kiban_areas)
    intersection["plateau_area"] = intersection["BuildingID"].map(plateau_areas)

    intersection["kiban_overlap_ratio"] = intersection["intersection_area"] / intersection["kiban_area"]
    intersection["plateau_overlap_ratio"] = intersection["intersection_area"] / intersection["plateau_area"]

    # 両方の重なり率が閾値以上のものを抽出
    return intersection[(intersection["kiban_overlap_ratio"] >= threshold) &
                        (intersection["plateau_overlap_ratio"] >= threshold)]

def process_by_town_with_full_output(kiban_gdf, plateau_gdf, output_folder, threshold=0.5):
    """
    町丁目ごとに一致判定を行い、基盤地図全体に一致結果を反映して町丁目ごとに保存。

    Args:
        kiban_gdf (GeoDataFrame): 基盤地図情報の建物ポリゴン。
        plateau_gdf (GeoDataFrame): プラトーの建物ポリゴン。
        output_folder (str): 結果を保存するフォルダ。
        threshold (float): 重なり面積の割合の閾値。

    Returns:
        None
    """
    os.makedirs(output_folder, exist_ok=True)
    
    # 基盤地図データとプラトーデータを投影座標系に変換
    kiban_gdf = kiban_gdf.to_crs(epsg=6677)
    plateau_gdf = plateau_gdf.to_crs(epsg=6677)

    # 基盤地図に新しい列を追加（初期値はNone）
    kiban_gdf["Usage"] = None
    kiban_gdf["TotalArea"] = None

    towns = kiban_gdf["Name_1"].unique()

    for town_name in towns:
        print(f"Processing town: {town_name}")

        # 該当町丁目データのフィルタリング
        town_kiban = kiban_gdf[kiban_gdf["Name_1"] == town_name].copy()
        town_plateau = plateau_gdf[plateau_gdf["Name"] == town_name]

        if len(town_kiban) == 0:
            print(f"No buildings found in kiban data for town: {town_name}")
            continue

        # 一次判定
        exact_matches = exact_match(town_kiban, town_plateau)
        for _, match_row in exact_matches.iterrows():
            plateau_row = town_plateau.loc[town_plateau["BuildingID"] == match_row["plateau_id"]]
            if len(plateau_row) > 0:
                town_kiban.loc[town_kiban["gml_id"] == match_row["kiban_id"], "Usage"] = plateau_row["Usage"].values[0]
                town_kiban.loc[town_kiban["gml_id"] == match_row["kiban_id"], "TotalArea"] = plateau_row["TotalArea"].values[0]

        # 残りの基盤地図建物
        remaining_kiban = town_kiban[~town_kiban["gml_id"].isin(exact_matches["kiban_id"])]

        # 二次判定
        significant_overlap_matches = significant_overlap(remaining_kiban, town_plateau, threshold)
        for _, match_row in significant_overlap_matches.iterrows():
            plateau_row = town_plateau.loc[town_plateau["BuildingID"] == match_row["BuildingID"]]
            if len(plateau_row) > 0:
                town_kiban.loc[town_kiban["gml_id"] == match_row["gml_id"], "Usage"] = plateau_row["Usage"].values[0]
                town_kiban.loc[town_kiban["gml_id"] == match_row["gml_id"], "TotalArea"] = plateau_row["TotalArea"].values[0]

        # 町丁目ごとの結果を保存
        output_path = os.path.join(output_folder, f"{town_name}_一致統合.shp")
        town_kiban.to_file(output_path, driver="ESRI Shapefile")
        print(f"Saved results for town: {town_name} to {output_path}")

# データの読み込み
kiban_gdf = gpd.read_file("基盤地図情報/博多区建物ポリゴン_2010_町丁目付加.shp")
plateau_gdf = gpd.read_file("PLATEAU/博多区PLATEAU_除外_町丁目付加.shp")

# 出力フォルダ
output_folder = "建物一致/町丁目_一致統合"

# メイン処理
process_by_town_with_full_output(kiban_gdf, plateau_gdf, output_folder, threshold=0.7)
