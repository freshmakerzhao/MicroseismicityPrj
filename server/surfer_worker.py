import os
import subprocess
import time

import pythoncom
import win32com.client


RISK_POST_LAYERS = [
    ("none", 0.0, 0.25, 0xFFFF00, 0.08),
    ("weak", 0.25, 0.5, 0x00FFFF, 0.1),
    ("medium", 0.5, 0.75, 0x008CFF, 0.12),
    ("strong", 0.75, float("inf"), 0x0000FF, 0.14),
]


def run_surfer_complete(
    data_file,
    output_folder=None,
    output_name=None,
    x_col=4,
    y_col=3,
    z_col=7,
    surfer_prog_id="Surfer.Application",
    surfer_exe_path="",
    clr_path="",
    visible=False,
    screen_updating=False,
):
    pythoncom.CoInitialize()
    app = None
    post_data_files = []
    try:
        abs_data_path = os.path.abspath(data_file)
        if not os.path.exists(abs_data_path):
            raise FileNotFoundError(f"Data file not found: {abs_data_path}")

        path_root = os.path.splitext(abs_data_path)[0]
        grid_file = path_root + ".grd"
        if output_folder:
            if output_name:
                output_png = os.path.join(output_folder, output_name)
            else:
                output_png = os.path.join(output_folder, os.path.basename(path_root) + ".png")
        else:
            output_png = path_root + ".png"

        for old_file in (grid_file, output_png):
            if os.path.exists(old_file):
                os.remove(old_file)

        try:
            app = win32com.client.DispatchEx(surfer_prog_id)
        except Exception:
            if surfer_exe_path and os.path.exists(surfer_exe_path):
                subprocess.Popen([surfer_exe_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(3)
                app = win32com.client.Dispatch(surfer_prog_id)
            else:
                raise RuntimeError(
                    f"Cannot create Surfer COM object with ProgID '{surfer_prog_id}'. "
                    "Please verify Surfer installation or set surfer.exe_path in config."
                )

        app.Visible = bool(visible)
        app.ScreenUpdating = bool(screen_updating)

        print(
            "Generating grid with Surfer GridData: "
            f"data={abs_data_path}, xCol={x_col}, yCol={y_col}, zCol={z_col}"
        )
        app.GridData(
            DataFile=abs_data_path,
            xCol=x_col,
            yCol=y_col,
            zCol=z_col,
            Algorithm=2,
            OutGrid=grid_file,
            ShowReport=False,
        )

        if not os.path.exists(grid_file):
            raise RuntimeError(f"Surfer grid file was not generated: {grid_file}")

        plot_doc = app.Documents.Add(1)
        map_frame = plot_doc.Shapes.AddContourMap(GridFileName=grid_file)
        contour_layer = map_frame.Overlays(1)

        if clr_path and os.path.exists(clr_path):
            contour_layer.FillForegroundColorMap.LoadFile(clr_path)
            print(f"Loaded color scale: {clr_path}")
        else:
            print("No valid color scale configured; using Surfer default")

        contour_layer.ApplyFillToLevels(FirstIndex=1, NumberToSet=1, NumberToSkip=0)
        contour_layer.FillContours = True
        contour_layer.ShowColorScale = True

        print("Adding W risk post map layers")
        post_data_files = _write_risk_post_files(abs_data_path, z_col)
        post_map_frames = []
        for post_file, color, symbol_size in post_data_files:
            post_map_frame = plot_doc.Shapes.AddPostMap(DataFileName=post_file)
            post_layer = post_map_frame.Overlays(1)
            post_layer.xCol = x_col
            post_layer.yCol = y_col
            post_layer.Symbol.Index = 12
            post_layer.Symbol.Size = symbol_size
            post_layer.Symbol.FillColor = color
            post_layer.Symbol.LineColor = 0x000000
            post_map_frames.append(post_map_frame)

        if not post_map_frames:
            post_map_frame = plot_doc.Shapes.AddPostMap(DataFileName=abs_data_path)
            post_layer = post_map_frame.Overlays(1)
            post_layer.xCol = x_col
            post_layer.yCol = y_col
            post_layer.Symbol.Index = 12
            post_layer.Symbol.Size = 0.1
            post_layer.Symbol.FillColor = 0xFFFF00
            post_map_frames.append(post_map_frame)

        print("Overlaying map layers")
        plot_doc.Selection.DeselectAll()
        map_frame.Selected = True
        for post_map_frame in post_map_frames:
            post_map_frame.Selected = True
        plot_doc.Selection.OverlayMaps()

        print(f"Exporting Surfer image: {output_png}")
        plot_doc.Export(FileName=output_png)
        if not os.path.exists(output_png):
            raise RuntimeError(f"Surfer export failed: {output_png}")

        plot_doc.Close(2)
        print("Surfer processing completed")
    except Exception as exc:
        raise RuntimeError(f"Surfer execution failed: {exc}") from exc
    finally:
        if app:
            app.Quit()
        for post_file, _, _ in post_data_files:
            if os.path.exists(post_file):
                os.remove(post_file)
        pythoncom.CoUninitialize()


def _write_risk_post_files(data_file, z_col):
    buckets = {name: [] for name, _, _, _, _ in RISK_POST_LAYERS}
    with open(data_file, "r", encoding="ascii") as fp:
        for line in fp:
            stripped = line.strip()
            if not stripped:
                continue
            parts = stripped.split()
            if len(parts) < z_col:
                continue
            try:
                w_value = float(parts[z_col - 1])
            except ValueError:
                continue

            for name, min_w, max_w, _, _ in RISK_POST_LAYERS:
                if min_w <= w_value < max_w:
                    buckets[name].append(stripped)
                    break

    path_root = os.path.splitext(data_file)[0]
    post_files = []
    for name, _, _, color, symbol_size in RISK_POST_LAYERS:
        rows = buckets[name]
        if not rows:
            continue
        post_file = f"{path_root}_{name}.dat"
        with open(post_file, "w", encoding="ascii", newline="\n") as fp:
            fp.write("\n".join(rows))
            fp.write("\n")
        post_files.append((post_file, color, symbol_size))
    return post_files


if __name__ == "__main__":
    sample_data = r"E:\Workspace_school\vue-echarts-master\资料\数据源\红阳矿区微震预警判据.xls"
    if os.path.exists(sample_data):
        run_surfer_complete(sample_data)
    else:
        print("Sample data file not found")
