import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

import flet as ft
from flet_charts import ChartAxis, ChartAxisLabel, LineChart, LineChartData, LineChartDataPoint
from flet_webview import WebView


DATA_FILE = Path.home() / ".stopwatch_history.json"


def format_elapsed(total_seconds: float) -> str:
    total_milliseconds = int(round(total_seconds * 100))
    centiseconds = total_milliseconds % 100
    total_seconds_int = total_milliseconds // 100
    hours, remainder = divmod(total_seconds_int, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"


def load_history():
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [
                item
                for item in data
                if isinstance(item, dict)
                and isinstance(item.get("elapsed"), (int, float))
                and isinstance(item.get("timestamp"), str)
                and isinstance(item.get("duration"), str)
            ][:20]
    except (OSError, json.JSONDecodeError):
        pass
    return []


def save_history(history):
    DATA_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


def add_history_entry(history, elapsed: float):
    entry = {
        "elapsed": round(float(elapsed), 2),
        "duration": format_elapsed(elapsed),
        "timestamp": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
    }
    history.insert(0, entry)
    history = history[:20]
    save_history(history)
    return history


def average_history(history):
    if not history:
        return 0.0
    return sum(item.get("elapsed", 0.0) for item in history) / len(history)


def clear_history():
    if DATA_FILE.exists():
        DATA_FILE.unlink()
    return []


async def main(page: ft.Page):
    page.title = "Stopwatch"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F5F7F3"
    page.padding = 24
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    elapsed = 0.0
    running = False
    started_at = 0.0
    timer_task = None
    laps = []
    history = load_history()

    display = ft.Text("00:00:00.00", size=58, weight=ft.FontWeight.BOLD, color="#1F2D2A")
    lap_list = ft.Column(spacing=8, height=140, scroll=ft.ScrollMode.AUTO)
    history_list = ft.Column(spacing=8, height=150, scroll=ft.ScrollMode.AUTO)
    summary_text = ft.Text("平均: 0.00秒", size=14, color="#4A6157", max_lines=1)
    history_chart = LineChart(
        width=380,
        height=200,
        min_x=0,
        min_y=0,
        left_axis=ChartAxis(title=ft.Text("秒", rotate=1.5708), label_size=36),
        bottom_axis=ChartAxis(label_size=28),
        horizontal_grid_lines=None,
    )

    def update_display():
        current_value = elapsed if not running else elapsed + (time.perf_counter() - started_at)
        display.value = format_elapsed(current_value)

    async def timer_loop():
        while running:
            update_display()
            page.update()
            await asyncio.sleep(0.05)

    def start_or_pause(_):
        nonlocal running, started_at, elapsed, timer_task, history

        if running:
            elapsed += time.perf_counter() - started_at
            running = False
            if timer_task is not None:
                timer_task.cancel()
                timer_task = None
            start_button.text = "開始"
            start_button.icon = ft.Icons.PLAY_ARROW_ROUNDED
            history = add_history_entry(history, elapsed)
            elapsed = 0.0
            render_history()
        else:
            running = True
            started_at = time.perf_counter()
            timer_task = asyncio.create_task(timer_loop())
            start_button.text = "一時停止"
            start_button.icon = ft.Icons.PAUSE_ROUNDED

        update_display()
        page.update()

    def add_lap(_):
        nonlocal laps
        if not running and elapsed == 0 and not laps:
            return

        current = elapsed if not running else elapsed + (time.perf_counter() - started_at)
        laps.insert(0, {"index": len(laps) + 1, "time": current})
        lap_entries = [
            ft.Row(
                [
                    ft.Text(f"Lap {lap['index']}", color="#4A6157", weight=ft.FontWeight.W_600),
                    ft.Text(format_elapsed(lap["time"]), color="#1F2D2A"),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
            for lap in laps
        ]
        lap_list.controls = lap_entries
        page.update()

    def reset_timer(_):
        nonlocal elapsed, running, started_at, timer_task, laps

        if timer_task is not None:
            timer_task.cancel()
            timer_task = None

        running = False
        elapsed = 0.0
        started_at = 0.0
        laps = []
        lap_list.controls.clear()
        display.value = "00:00:00.00"
        start_button.text = "開始"
        start_button.icon = ft.Icons.PLAY_ARROW_ROUNDED
        page.update()

    def record_elapsed(_):
        nonlocal elapsed, started_at, history
        current = elapsed if not running else elapsed + (time.perf_counter() - started_at)
        if current <= 0:
            return
        history = add_history_entry(history, current)
        render_history()

    def delete_history_entry(index: int):
        nonlocal history
        if 0 <= index < len(history):
            del history[index]
            save_history(history)
            render_history()

    def clear_all_history(_):
        nonlocal history
        history = clear_history()
        render_history()

    def render_history():
        avg_value = average_history(history)
        summary_text.value = f"平均: {avg_value:.2f}秒"

        chronological_history = list(reversed(history))
        history_chart.visible = bool(chronological_history)
        history_chart.data_series = [
            LineChartData(
                color="#3D8B70",
                stroke_width=3,
                point=True,
                points=[
                    LineChartDataPoint(
                        x=index,
                        y=item["elapsed"],
                        tooltip=f"{item['duration']}\n{item['timestamp']}",
                    )
                    for index, item in enumerate(chronological_history, start=1)
                ],
            ),
            LineChartData(
                color="#CF6048",
                stroke_width=2,
                dash_pattern=[6, 4],
                point=False,
                points=[
                    LineChartDataPoint(x=0, y=avg_value),
                    LineChartDataPoint(
                        x=max(2, len(chronological_history) + 1),
                        y=avg_value,
                    ),
                ],
            ),
        ] if chronological_history else []
        history_chart.max_x = max(2, len(chronological_history) + 1)
        history_chart.max_y = max(
            1,
            max((item["elapsed"] for item in chronological_history), default=0) * 1.15,
        )
        history_chart.bottom_axis = ChartAxis(
            labels=[
                ChartAxisLabel(value=index, label=str(index))
                for index in range(1, len(chronological_history) + 1)
            ],
            label_size=28,
        )

        if not history:
            history_list.controls = [
                ft.Text("まだ記録がありません", color="#809188", size=12),
            ]
            page.update()
            return

        history_list.controls = [
            ft.Row(
                [
                    ft.Text(f"{index}.", width=24, color="#4A6157", weight=ft.FontWeight.W_600),
                    ft.Text(item["duration"], color="#1F2D2A"),
                    ft.Text(item["timestamp"], color="#809188", size=10),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_color="#CF6048",
                        tooltip="削除",
                        on_click=lambda _, i=index - 1: delete_history_entry(i),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
            for index, item in enumerate(history, start=1)
        ]
        page.update()

    start_button = ft.Button(
        "開始",
        icon=ft.Icons.PLAY_ARROW_ROUNDED,
        on_click=start_or_pause,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
    )
    lap_button = ft.OutlinedButton("ラップ", icon=ft.Icons.TIMER_OUTLINED, on_click=add_lap)
    record_button = ft.TextButton("記録", icon=ft.Icons.SAVE_ALT_ROUNDED, on_click=record_elapsed)
    clear_history_button = ft.TextButton("履歴削除", icon=ft.Icons.DELETE_SWEEP_ROUNDED, on_click=clear_all_history)
    reset_button = ft.Button(
        "リセット",
        icon=ft.Icons.RESTART_ALT_ROUNDED,
        on_click=reset_timer,
        width=132,
        style=ft.ButtonStyle(
            bgcolor="#FCE8E4",
            color="#A63D2F",
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
    )

    content = ft.ResponsiveRow(
        controls=[
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Stopwatch", size=22, weight=ft.FontWeight.W_600, color="#2D4F45"),
                        display,
                        ft.Row(
                            [
                                start_button,
                                lap_button,
                                record_button,
                                clear_history_button,
                                reset_button,
                            ],
                            spacing=8,
                            wrap=True,
                            run_spacing=8,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text("Laps", size=16, weight=ft.FontWeight.W_600, color="#2D4F45"),
                                    lap_list,
                                ],
                                spacing=8,
                            ),
                            width=420,
                            bgcolor="#FFFFFF",
                            border_radius=18,
                            padding=20,
                            shadow=ft.BoxShadow(blur_radius=20, color="#D7E0D9", offset=ft.Offset(0, 8)),
                        ),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text("記録履歴", size=16, weight=ft.FontWeight.W_600, color="#2D4F45"),
                                    ft.Container(content=summary_text, height=28),
                                    history_chart,
                                    history_list,
                                ],
                                spacing=8,
                            ),
                            width=420,
                            bgcolor="#FFFFFF",
                            border_radius=18,
                            padding=20,
                            shadow=ft.BoxShadow(blur_radius=20, color="#D7E0D9", offset=ft.Offset(0, 8)),
                        ),
                    ],
                    spacing=18,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                col={ft.ResponsiveRowBreakpoint.XS: 12, ft.ResponsiveRowBreakpoint.LG: 6},
            ),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("音声文字起こし", size=18, weight=ft.FontWeight.W_600, color="#2D4F45"),
                        WebView(url="/transcriber.html?embed=1", expand=True, height=780),
                    ],
                    spacing=12,
                    expand=True,
                ),
                col={ft.ResponsiveRowBreakpoint.XS: 12, ft.ResponsiveRowBreakpoint.LG: 6},
                height=860,
                bgcolor="#FFFFFF",
                border_radius=18,
                padding=20,
                shadow=ft.BoxShadow(blur_radius=20, color="#D7E0D9", offset=ft.Offset(0, 8)),
            ),
        ],
        columns=12,
        spacing=20,
        run_spacing=20,
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.START,
        expand=True,
    )

    page.add(content)
    render_history()
    update_display()


if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER, port=0)
