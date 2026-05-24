#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk
import importlib
from typing import Optional

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy

class JoyGuiPublisher(Node):
    def __init__(self) -> None:
        super().__init__('joy_gui_publisher')

        self.declare_parameter('joy_topic', '/joy')
        self.declare_parameter('publish_rate_hz', 20.0)
        self.declare_parameter('control_mode_service', '/drone/set_control_mode')
        self.declare_parameter('position_target_service', '/drone/set_position_target')
        self.declare_parameter('mode_toggle_button', 6)
        self.declare_parameter('mode_reset_button', 7)
        self.declare_parameter('target_step_xy_m', 0.10)
        self.declare_parameter('target_step_z_m', 0.05)
        self.declare_parameter('target_step_yaw_deg', 10.0)

        self._joy_topic = self.get_parameter('joy_topic').value or '/joy'
        self._publish_rate_hz = float(self.get_parameter('publish_rate_hz').value or 20.0)
        self._publish_period_ms = max(20, int(1000.0 / self._publish_rate_hz))
        self._control_mode_service = self.get_parameter('control_mode_service').value or '/drone/set_control_mode'
        self._position_target_service = self.get_parameter('position_target_service').value or '/drone/set_position_target'
        self._mode_toggle_button = int(self.get_parameter('mode_toggle_button').value or 6)
        self._mode_reset_button = int(self.get_parameter('mode_reset_button').value or 7)
        self._target_step_xy_m = float(self.get_parameter('target_step_xy_m').value or 0.10)
        self._target_step_z_m = float(self.get_parameter('target_step_z_m').value or 0.05)
        self._target_step_yaw_deg = float(self.get_parameter('target_step_yaw_deg').value or 10.0)

        self._publisher = self.create_publisher(Joy, self._joy_topic, 10)
        self._control_mode_client = None
        self._position_target_client = None

        self._window = tk.Tk()
        self._window.title('Drone Control')
        self._window.geometry('760x640')
        self._window.minsize(720, 600)
        self._window.protocol('WM_DELETE_WINDOW', self._on_close)
        self._window.configure(bg='#0f172a')

        self._roll = tk.DoubleVar(value=0.0)
        self._pitch = tk.DoubleVar(value=0.0)
        self._yaw = tk.DoubleVar(value=0.0)
        self._throttle = tk.DoubleVar(value=-1.0)
        self._deadman = tk.IntVar(value=1)
        self._deadman_state = tk.StringVar(value='ON')
        self._mode_label = tk.StringVar(value='manual_attitude')
        self._status = tk.StringVar(value='Ready')
        self._service_state = tk.StringVar(value='Services: connecting...')
        self._target_state = tk.StringVar(value='Target: x=0.00 y=0.00 z=0.00 yaw=0.0°')
        self._target_x = tk.StringVar(value='0.00')
        self._target_y = tk.StringVar(value='0.00')
        self._target_z = tk.StringVar(value='0.00')
        self._target_yaw_deg = tk.StringVar(value='0.0')
        self._pulse_mode_toggle = False
        self._pulse_mode_reset = False

        self._setup_styles()
        self._build_ui()
        self._window.bind('<space>', lambda _event: self._toggle_deadman())
        self._window.bind('m', lambda _event: self._request_mode_toggle())
        self._window.bind('r', lambda _event: self._request_mode_reset())
        self._window.bind('0', lambda _event: self._reset())

    def _setup_styles(self) -> None:
        style = ttk.Style(self._window)
        style.theme_use('clam')
        style.configure('Root.TFrame', background='#0f172a')
        style.configure('Card.TFrame', background='#111827', relief='flat')
        style.configure('Title.TLabel', background='#0f172a', foreground='#e5e7eb', font=('TkDefaultFont', 18, 'bold'))
        style.configure('Subtitle.TLabel', background='#0f172a', foreground='#94a3b8', font=('TkDefaultFont', 10))
        style.configure('CardTitle.TLabel', background='#111827', foreground='#f8fafc', font=('TkDefaultFont', 11, 'bold'))
        style.configure('CardText.TLabel', background='#111827', foreground='#cbd5e1', font=('TkDefaultFont', 10))
        style.configure('Mode.TLabel', background='#111827', foreground='#38bdf8', font=('TkDefaultFont', 11, 'bold'))
        style.configure('Value.TLabel', background='#111827', foreground='#e2e8f0', font=('TkDefaultFont', 9, 'bold'))
        style.configure('Accent.TButton', padding=(10, 7), font=('TkDefaultFont', 10, 'bold'))
        style.configure('Small.TButton', padding=(8, 5))
        style.map('Accent.TButton', foreground=[('active', '#ffffff')])

    def _build_ui(self) -> None:
        container = ttk.Frame(self._window, style='Root.TFrame', padding=14)
        container.pack(fill='both', expand=True)

        ttk.Label(container, text='Drone Control', style='Title.TLabel').pack(anchor='w')
        ttk.Label(
            container,
            text='Space toggles deadman, M toggles mode, R recenters target, 0 resets axes.',
            style='Subtitle.TLabel',
        ).pack(anchor='w', pady=(4, 12))

        top_row = ttk.Frame(container, style='Root.TFrame')
        top_row.pack(fill='x', pady=(0, 10))
        self._build_mode_card(top_row)
        self._build_live_card(top_row)

        bottom_row = ttk.Frame(container, style='Root.TFrame')
        bottom_row.pack(fill='both', expand=True)
        self._build_axes_card(bottom_row)
        self._build_target_card(bottom_row)

        footer = ttk.Frame(container, style='Root.TFrame')
        footer.pack(fill='x', pady=(10, 0))
        ttk.Label(footer, textvariable=self._status, style='Subtitle.TLabel').pack(anchor='w')

    def _build_mode_card(self, parent: ttk.Frame) -> None:
        card = ttk.Frame(parent, style='Card.TFrame', padding=12)
        card.pack(side='left', fill='both', expand=True, padx=(0, 6))

        ttk.Label(card, text='Mode', style='CardTitle.TLabel').pack(anchor='w')
        ttk.Label(card, textvariable=self._mode_label, style='Mode.TLabel').pack(anchor='w', pady=(2, 8))

        row = ttk.Frame(card, style='Card.TFrame')
        row.pack(fill='x')
        ttk.Button(row, text='Manual', style='Accent.TButton', command=lambda: self._set_control_mode(0, 'manual_attitude')).pack(side='left', padx=(0, 6))
        ttk.Button(row, text='Hold', style='Accent.TButton', command=lambda: self._set_control_mode(1, 'position_hold')).pack(side='left')

        row2 = ttk.Frame(card, style='Card.TFrame')
        row2.pack(fill='x', pady=(8, 0))
        ttk.Button(row2, text='Toggle (M)', style='Small.TButton', command=self._request_mode_toggle).pack(side='left', padx=(0, 6))
        ttk.Button(row2, text='Reset (R)', style='Small.TButton', command=self._request_mode_reset).pack(side='left')

        ttk.Label(card, textvariable=self._service_state, style='CardText.TLabel', wraplength=260, justify='left').pack(anchor='w', pady=(8, 0))

    def _build_live_card(self, parent: ttk.Frame) -> None:
        card = ttk.Frame(parent, style='Card.TFrame', padding=12)
        card.pack(side='left', fill='both', expand=True, padx=(6, 0))

        ttk.Label(card, text='Live', style='CardTitle.TLabel').pack(anchor='w')
        box = ttk.Frame(card, style='Card.TFrame')
        box.pack(fill='x', pady=(6, 0))
        ttk.Label(box, text='Deadman', style='CardText.TLabel').grid(row=0, column=0, sticky='w')
        ttk.Label(box, textvariable=self._deadman_state, style='Value.TLabel').grid(row=0, column=1, sticky='e')
        ttk.Label(box, text='Mode button', style='CardText.TLabel').grid(row=1, column=0, sticky='w')
        ttk.Label(box, text=str(self._mode_toggle_button), style='Value.TLabel').grid(row=1, column=1, sticky='e')
        ttk.Label(box, text='Reset button', style='CardText.TLabel').grid(row=2, column=0, sticky='w')
        ttk.Label(box, text=str(self._mode_reset_button), style='Value.TLabel').grid(row=2, column=1, sticky='e')

    def _build_axes_card(self, parent: ttk.Frame) -> None:
        card = ttk.Frame(parent, style='Card.TFrame', padding=12)
        card.pack(side='left', fill='both', expand=True, padx=(0, 6))

        ttk.Label(card, text='Axes', style='CardTitle.TLabel').pack(anchor='w')
        self._add_axis_slider(card, 'Roll', self._roll)
        self._add_axis_slider(card, 'Pitch', self._pitch)
        self._add_axis_slider(card, 'Yaw', self._yaw)
        self._add_axis_slider(card, 'Throttle', self._throttle)

        row = ttk.Frame(card, style='Card.TFrame')
        row.pack(fill='x', pady=(8, 0))
        ttk.Checkbutton(row, text='Deadman', variable=self._deadman).pack(side='left')
        ttk.Button(row, text='Zero', style='Small.TButton', command=self._reset).pack(side='right')

    def _build_target_card(self, parent: ttk.Frame) -> None:
        card = ttk.Frame(parent, style='Card.TFrame', padding=12)
        card.pack(side='left', fill='both', expand=True, padx=(6, 0))

        ttk.Label(card, text='Target', style='CardTitle.TLabel').pack(anchor='w')
        grid = ttk.Frame(card, style='Card.TFrame')
        grid.pack(fill='x', pady=(4, 0))
        self._add_target_entry(grid, 0, 'X', self._target_x)
        self._add_target_entry(grid, 1, 'Y', self._target_y)
        self._add_target_entry(grid, 2, 'Z', self._target_z)
        self._add_target_entry(grid, 3, 'Yaw', self._target_yaw_deg)

        row = ttk.Frame(card, style='Card.TFrame')
        row.pack(fill='x', pady=(8, 0))
        ttk.Button(row, text='Apply', style='Accent.TButton', command=self._apply_position_target).pack(side='left', padx=(0, 6))
        ttk.Button(row, text='Use current', style='Small.TButton', command=self._request_mode_reset).pack(side='left', padx=(0, 6))
        ttk.Button(row, text='Hold', style='Small.TButton', command=lambda: self._set_control_mode(1, 'position_hold')).pack(side='left')

        nudge = ttk.Frame(card, style='Card.TFrame')
        nudge.pack(fill='x', pady=(8, 0))
        ttk.Button(nudge, text='+XY', style='Small.TButton', command=lambda: self._nudge_target(self._target_step_xy_m, 0.0, 0.0, 0.0)).pack(side='left', padx=(0, 4))
        ttk.Button(nudge, text='-XY', style='Small.TButton', command=lambda: self._nudge_target(-self._target_step_xy_m, 0.0, 0.0, 0.0)).pack(side='left', padx=(0, 4))
        ttk.Button(nudge, text='+Z', style='Small.TButton', command=lambda: self._nudge_target(0.0, 0.0, self._target_step_z_m, 0.0)).pack(side='left', padx=(0, 4))
        ttk.Button(nudge, text='-Z', style='Small.TButton', command=lambda: self._nudge_target(0.0, 0.0, -self._target_step_z_m, 0.0)).pack(side='left', padx=(0, 4))
        ttk.Button(nudge, text='+Yaw', style='Small.TButton', command=lambda: self._nudge_target(0.0, 0.0, 0.0, self._target_step_yaw_deg)).pack(side='left', padx=(0, 4))
        ttk.Button(nudge, text='-Yaw', style='Small.TButton', command=lambda: self._nudge_target(0.0, 0.0, 0.0, -self._target_step_yaw_deg)).pack(side='left')

        ttk.Label(card, textvariable=self._target_state, style='Mode.TLabel').pack(anchor='w', pady=(8, 0))

    def _add_axis_slider(self, parent: ttk.Frame, label: str, variable: tk.DoubleVar) -> None:
        frame = ttk.Frame(parent, style='Card.TFrame')
        frame.pack(fill='x', pady=4)
        ttk.Label(frame, text=label, style='CardText.TLabel', width=10).pack(side='left')
        scale = ttk.Scale(frame, from_=-1.0, to=1.0, variable=variable)
        scale.pack(side='left', fill='x', expand=True, padx=(6, 6))
        value = ttk.Label(frame, text=f'{variable.get():.2f}', style='Value.TLabel', width=6)
        value.pack(side='right')

        def sync_value(*_args: object) -> None:
            value.configure(text=f'{variable.get():.2f}')

        variable.trace_add('write', sync_value)
        sync_value()

    def _add_target_entry(self, parent: ttk.Frame, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label, style='CardText.TLabel').grid(row=row, column=0, sticky='w', pady=2)
        ttk.Entry(parent, textvariable=variable, width=10).grid(row=row, column=1, sticky='w', padx=(6, 0), pady=2)

    def _build_message(self) -> Joy:
        message = Joy()
        message.axes = [
            float(self._roll.get()),
            float(self._pitch.get()),
            float(self._yaw.get()),
            float(self._throttle.get()),
        ]
        buttons = [0, 0, 0, 0, int(self._deadman.get()), 0, 0, 0]
        if self._pulse_mode_toggle:
            buttons[self._mode_toggle_button] = 1
        if self._pulse_mode_reset:
            buttons[self._mode_reset_button] = 1
        message.buttons = buttons
        return message

    def _publish(self) -> None:
        message = self._build_message()
        self._publisher.publish(message)
        self._pulse_mode_toggle = False
        self._pulse_mode_reset = False
        self._deadman_state.set('ON' if self._deadman.get() else 'OFF')
        self._status.set('Publishing roll={:.2f} pitch={:.2f} yaw={:.2f} throttle={:.2f}'.format(
            message.axes[0], message.axes[1], message.axes[2], message.axes[3]
        ))

    def _reset(self) -> None:
        self._roll.set(0.0)
        self._pitch.set(0.0)
        self._yaw.set(0.0)
        self._throttle.set(-1.0)
        self._deadman.set(0)
        self._publish()

    def _toggle_deadman(self) -> None:
        self._deadman.set(0 if self._deadman.get() else 1)
        self._publish()

    def _request_mode_toggle(self) -> None:
        self._pulse_mode_toggle = True
        self._mode_label.set('toggle queued')
        self._publish()

    def _request_mode_reset(self) -> None:
        self._pulse_mode_reset = True
        self._mode_label.set('reset queued')
        self._publish()

    def _set_feedback(self, service_text: str, status_text: Optional[str] = None, mode_text: Optional[str] = None) -> None:
        self._service_state.set(service_text)
        if status_text is not None:
            self._status.set(status_text)
        if mode_text is not None:
            self._mode_label.set(mode_text)

    def _set_control_mode(self, mode: int, mode_name: str) -> None:
        service_type = self._load_service_type('SetControlMode')
        if service_type is None:
            self._set_feedback('control mode service type unavailable', 'Control mode service type is unavailable.')
            return

        client = self._ensure_control_mode_client(service_type)
        if client is None or not client.wait_for_service(timeout_sec=0.1):
            self._set_feedback('control mode service unavailable', 'Control mode service is not available.')
            return

        request = service_type.Request()
        request.mode = mode
        future = client.call_async(request)
        self._set_feedback(f'sending mode: {mode_name}')

        def on_done(done_future) -> None:
            try:
                response = done_future.result()
            except Exception as exc:  # pragma: no cover - runtime safety
                self._window.after(0, lambda: self._set_feedback(str(exc), 'Control mode request failed.'))
                return

            self._window.after(0, lambda: self._set_feedback(
                response.message or f'Control mode set to {mode_name}',
                f'Control mode: {mode_name}',
                mode_name,
            ))

        future.add_done_callback(on_done)

    def _set_position_target(self, x: float, y: float, z: float, yaw_deg: float) -> None:
        service_type = self._load_service_type('SetPositionTarget')
        if service_type is None:
            self._set_feedback('position target service type unavailable', 'Position target service type is unavailable.')
            return

        client = self._ensure_position_target_client(service_type)
        if client is None or not client.wait_for_service(timeout_sec=0.1):
            self._set_feedback('position target service unavailable', 'Position target service is not available.')
            return

        request = service_type.Request()
        request.x = x
        request.y = y
        request.z = z
        request.yaw_deg = yaw_deg
        future = client.call_async(request)
        self._set_feedback('sending target...')

        def on_done(done_future) -> None:
            try:
                response = done_future.result()
            except Exception as exc:  # pragma: no cover - runtime safety
                self._window.after(0, lambda: self._set_feedback(str(exc), 'Position target request failed.'))
                return

            self._window.after(0, lambda: self._set_feedback(
                response.message or 'Position target set',
                f'Position target updated: x={x:.2f} y={y:.2f} z={z:.2f} yaw={yaw_deg:.1f}°',
                self._mode_label.get(),
            ))
            self._window.after(0, lambda: self._target_state.set(
                f'Target: x={x:.2f} y={y:.2f} z={z:.2f} yaw={yaw_deg:.1f}°'
            ))

        future.add_done_callback(on_done)

    def _read_float_var(self, variable: tk.StringVar, label: str) -> Optional[float]:
        try:
            return float(variable.get())
        except ValueError:
            self._set_feedback(f'Invalid {label} value', f'Invalid target input for {label}.')
            return None

    def _load_service_type(self, symbol: str):
        try:
            module = importlib.import_module('drone_control.srv')
            return getattr(module, symbol)
        except (ImportError, AttributeError):
            return None

    def _ensure_control_mode_client(self, service_type):
        if self._control_mode_client is None:
            self._control_mode_client = self.create_client(service_type, self._control_mode_service)
        return self._control_mode_client

    def _ensure_position_target_client(self, service_type):
        if self._position_target_client is None:
            self._position_target_client = self.create_client(service_type, self._position_target_service)
        return self._position_target_client

    def _apply_position_target(self) -> None:
        x = self._read_float_var(self._target_x, 'X')
        y = self._read_float_var(self._target_y, 'Y')
        z = self._read_float_var(self._target_z, 'Z')
        yaw_deg = self._read_float_var(self._target_yaw_deg, 'Yaw')
        if x is None or y is None or z is None or yaw_deg is None:
            return
        self._set_position_target(x, y, z, yaw_deg)

    def _nudge_target(self, dx: float, dy: float, dz: float, dyaw_deg: float) -> None:
        x = self._read_float_var(self._target_x, 'X')
        y = self._read_float_var(self._target_y, 'Y')
        z = self._read_float_var(self._target_z, 'Z')
        yaw_deg = self._read_float_var(self._target_yaw_deg, 'Yaw')
        if x is None or y is None or z is None or yaw_deg is None:
            return

        x += dx
        y += dy
        z += dz
        yaw_deg += dyaw_deg
        self._target_x.set(f'{x:.2f}')
        self._target_y.set(f'{y:.2f}')
        self._target_z.set(f'{z:.2f}')
        self._target_yaw_deg.set(f'{yaw_deg:.1f}')
        self._set_position_target(x, y, z, yaw_deg)

    def _on_close(self) -> None:
        self._deadman.set(0)
        self._roll.set(0.0)
        self._pitch.set(0.0)
        self._yaw.set(0.0)
        self._throttle.set(-1.0)
        self._publish()
        self._window.destroy()
        self.destroy_node()
        rclpy.shutdown()

    def spin(self) -> None:
        def tick() -> None:
            if not rclpy.ok():
                return
            rclpy.spin_once(self, timeout_sec=0.0)
            self._publish()
            self._window.after(self._publish_period_ms, tick)

        tick()
        self._window.mainloop()


def main() -> None:
    rclpy.init()
    node = JoyGuiPublisher()
    try:
        node.spin()
    finally:
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()


if __name__ == '__main__':
    main()