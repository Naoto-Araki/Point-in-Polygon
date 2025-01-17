import os
from lxml import etree
import shapefile  # pyshpを使用

# GMLファイルが格納されているディレクトリ
input_dir = "PLATEAU/GML形式"  # GMLファイルのディレクトリ
output_dir = "PLATEAU/shp形式"  # Shapefileを保存するディレクトリ

# 名前空間の定義
nsmap = {
    "gml": "http://www.opengis.net/gml",
    "bldg": "http://www.opengis.net/citygml/building/2.0",
    "uro": "https://www.geospatial.jp/iur/uro/3.0",
    "core": "http://www.opengis.net/citygml/2.0"
}

# 入力ディレクトリ内のGMLファイルを処理
for gml_file in os.listdir(input_dir):
    if gml_file.endswith(".gml"):
        input_path = os.path.join(input_dir, gml_file)
        output_shp_name = os.path.splitext(gml_file)[0] + ".shp"
        output_shp_path = os.path.join(output_dir, output_shp_name)

        print(f"Processing file: {gml_file}")

        # XMLを解析
        tree = etree.parse(input_path)
        root = tree.getroot()

        # Shapefileの作成
        shp_writer = shapefile.Writer(output_shp_path)
        shp_writer.field("BuildingID", "C")  # 建物ID
        shp_writer.field("Year", "C")        # 建設年
        shp_writer.field("Usage", "C")       # 用途
        shp_writer.field("Height", "N", decimal=2)  # 高さ
        shp_writer.field("TotalArea", "N", decimal=2)  # 延床面積

        # 全ての bldg:Building 要素を取得
        buildings = root.findall(".//bldg:Building", namespaces=nsmap)
        print(f"  Total Buildings Found: {len(buildings)}")

        # 各建物の情報を取得
        for building in buildings:
            # 建物ID
            building_id = building.get("{http://www.opengis.net/gml}id")

            # 建設年
            year_of_construction = building.find("bldg:yearOfConstruction", namespaces=nsmap)
            year = year_of_construction.text if year_of_construction is not None else "Unknown"

            # 用途
            usage = building.find("bldg:usage", namespaces=nsmap)
            usage_text = usage.text if usage is not None else "Unknown"

            # 高さ
            height = building.find("bldg:measuredHeight", namespaces=nsmap)
            height_value = float(height.text) if height is not None else None

            # 延床面積
            total_area = building.find(".//uro:totalFloorArea", namespaces=nsmap)
            total_area_value = float(total_area.text) if total_area is not None else None

            # 建物ポリゴン（Lod0 Footprint）
            footprint = building.find(".//bldg:lod0FootPrint//gml:LinearRing/gml:posList", namespaces=nsmap)
            if footprint is None:
                footprint = building.find(".//bldg:lod0RoofEdge//gml:LinearRing/gml:posList", namespaces=nsmap)

            if footprint is not None:
                coordinates = footprint.text.strip().split()
                # 座標ペアを作成
                polygon = [
                    [tuple(map(float, coordinates[i:i+2])) for i in range(0, len(coordinates), 3)]
                ]

                # Shapefileに書き込み
                shp_writer.poly(polygon)
                shp_writer.record(
                    BuildingID=building_id,
                    Year=year,
                    Usage=usage_text,
                    Height=height_value,
                    TotalArea=total_area_value
                )

        # Shapefileを保存
        shp_writer.close()

        # CRS情報をPRJファイルに書き込む
        prj_path = output_shp_path.replace(".shp", ".prj")
        with open(prj_path, "w") as prj_file:
            prj_file.write(
                'GEOGCS["JGD2011",DATUM["Japanese Geodetic Datum 2011",SPHEROID["GRS 1980",6378137,298.257222101]],'
                'PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]'
            )

        print(f"  Shapefile saved to: {output_shp_path}")
        print(f"  CRS defined in: {prj_path}\n")
