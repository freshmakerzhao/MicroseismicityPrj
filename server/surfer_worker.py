import win32com.client
import pythoncom
import os
import subprocess
import time

def run_surfer_complete(
    data_file,
    output_folder=None,
    surfer_prog_id="Surfer.Application",
    surfer_exe_path="",
    clr_path="",
    visible=False,
    screen_updating=False,
):
    pythoncom.CoInitialize()
    app = None
    try:
        # 1. 初始化路径
        abs_data_path = os.path.abspath(data_file)
        if not os.path.exists(abs_data_path):
            raise FileNotFoundError(f"Data file not found: {abs_data_path}")

        path_root = os.path.splitext(abs_data_path)[0]
        grid_file = path_root + ".grd"
        
        # 如果指定了输出文件夹，则图片保存到该文件夹
        if output_folder:
            base_name = os.path.basename(path_root)
            output_png = os.path.join(output_folder, base_name + ".png")
        else:
            output_png = path_root + ".png"

        # 如果存在旧文件，先删除防止 Surfer 弹出覆盖确认框
        for f in [grid_file, output_png]:
            if os.path.exists(f): os.remove(f)

        # 2. 启动进程
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

        # 3. 网格化数据 (对应 BAS: GridData)
        print("正在生成网格 (GridData)...")
        # xCol=4(D列), yCol=3(C列), zCol=7(G列)
        app.GridData(
            DataFile=abs_data_path,
            xCol=4, yCol=3, zCol=7,
            Algorithm=2,      # Kriging 克里金
            OutGrid=grid_file,
            ShowReport=False
        )

        # 4. 创建绘图并添加等值线图
        plot_doc = app.Documents.Add(1)
        map_frame = plot_doc.Shapes.AddContourMap(GridFileName=grid_file)
        contour_layer = map_frame.Overlays(1)
        
        # 5. 加载色阶文件 (对应 BAS: FillForegroundColorMap.LoadFile)
        if clr_path and os.path.exists(clr_path):
            contour_layer.FillForegroundColorMap.LoadFile(clr_path)
            print(f"已从 {clr_path} 加载色阶")
        else:
            print("未配置有效色阶文件，使用默认色阶")
        
        # 6. 应用填充 (对应 BAS: ApplyFillToLevels + FillContours)
        contour_layer.ApplyFillToLevels(FirstIndex=1, NumberToSet=1, NumberToSkip=0)
        contour_layer.FillContours = True
        contour_layer.ShowColorScale = True

        # 7. 添加散点图层 (对应 BAS: AddPostMap)
        print("正在添加散点图层...")
        post_map_frame = plot_doc.Shapes.AddPostMap(DataFileName=abs_data_path)
        post_layer = post_map_frame.Overlays(1)
        
        # 配置散点样式
        post_layer.xCol = 4  # D列
        post_layer.yCol = 3  # C列
        post_layer.Symbol.Index = 12      # 符号样式
        post_layer.Symbol.Size = 0.1      # 符号大小
        post_layer.Symbol.FillColor = 0xFFFF00  # 青色 (srfColorCyan)

        # 8. 合并图层 (对应 BAS: OverlayMaps)
        print("正在合并图层...")
        plot_doc.Selection.DeselectAll()
        map_frame.Selected = True
        post_map_frame.Selected = True
        plot_doc.Selection.OverlayMaps()

        # 9. 导出图片
        print(f"正在导出最终图片: {output_png}")
        plot_doc.Export(FileName=output_png)
        if not os.path.exists(output_png):
            raise RuntimeError(f"Surfer export failed: {output_png}")
        
        # 10. 关闭文档
        plot_doc.Close(2) 
        print("后台处理完成！")

    except Exception as e:
        raise RuntimeError(f"Surfer execution failed: {e}") from e
    finally:
        if app:
            app.Quit()
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    my_data = r"E:\Workspace_school\vue-echarts-master\资料\红阳矿区微震预警判据.xls"
    if os.path.exists(my_data):
        run_surfer_complete(my_data)
    else:
        print("找不到文件")