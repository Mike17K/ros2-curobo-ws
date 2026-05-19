#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy


class JoyGuiPublisher(Node):
    def __init__(self) -> None:
        super().__init__('joy_gui_publisher')

        self.declare_parameter('joy_topic', '/joy')
        self.declare_parameter('publish_rate_hz', 20.0)

        self._joy_topic = self.get_parameter('joy_topic').value or '/joy'
        self._publish_rate_hz = float(self.get_parameter('publish_rate_hz').value or 20.0)
        self._publish_period_ms = max(20, int(1000.0 / self._publish_rate_hz))

        self._publisher = self.create_publisher(Joy, self._joy_topic, 10)
        self._window = tk.Tk()
        self._window.title('Drone Joy Publisher')
        self._window.geometry('420x420')
        self._window.minsize(420, 420)
        self._window.protocol('WM_DELETE_WINDOW', self._on_close)

        self._roll = tk.DoubleVar(value=0.0)
        self._pitch = tk.DoubleVar(value=0.0)
        self._yaw = tk.DoubleVar(value=0.0)
        self._throttle = tk.DoubleVar(value=-1.0)
        self._deadman = tk.IntVar(value=0)
        self._status = tk.StringVar(value='Ready')

        self._build_ui()

    def _build_ui(self) -> None:
        container = ttk.Frame(self._window, padding=12)
        container.pack(fill='both', expand=True)

        title = ttk.Label(container, text='Joystick Publisher', font=('TkDefaultFont', 16, 'bold'))
        title.pack(anchor='w', pady=(0, 8))

        subtitle = ttk.Label(
            container,
            text='Publishes sensor_msgs/msg/Joy on the configured topic.',
            wraplength=380,
        )
        subtitle.pack(anchor='w', pady=(0, 12))

        self._add_axis_slider(container, 'Roll', self._roll)
        self._add_axis_slider(container, 'Pitch', self._pitch)
        self._add_axis_slider(container, 'Yaw', self._yaw)
        self._add_axis_slider(container, 'Throttle', self._throttle)

        deadman_row = ttk.Frame(container)
        deadman_row.pack(fill='x', pady=(10, 4))
        ttk.Checkbutton(
            deadman_row,
            text='Deadman enabled',
            variable=self._deadman,
        ).pack(side='left')
        ttk.Button(deadman_row, text='Reset', command=self._reset).pack(side='right')

        ttk.Separator(container).pack(fill='x', pady=12)
        ttk.Label(container, textvariable=self._status).pack(anchor='w')
        ttk.Label(container, text=f'Topic: {self._joy_topic}').pack(anchor='w', pady=(4, 0))

    def _add_axis_slider(self, parent: ttk.Frame, label: str, variable: tk.DoubleVar) -> None:
        frame = ttk.Frame(parent)
        frame.pack(fill='x', pady=4)
        ttk.Label(frame, text=label, width=10).pack(side='left')
        scale = ttk.Scale(frame, from_=-1.0, to=1.0, variable=variable)
        scale.pack(side='left', fill='x', expand=True)
        value = ttk.Label(frame, textvariable=tk.StringVar(value='0.00'), width=8)
        value.pack(side='right')

        def sync_value(*_args: object) -> None:
            value.configure(text=f'{variable.get():.2f}')

        variable.trace_add('write', sync_value)
        sync_value()

    def _build_message(self) -> Joy:
        message = Joy()
        message.axes = [
            float(self._roll.get()),
            float(self._pitch.get()),
            float(self._yaw.get()),
            float(self._throttle.get()),
        ]
        message.buttons = [0, 0, 0, 0, int(self._deadman.get()), 0, 0, 0]
        return message

    def _publish(self) -> None:
        message = self._build_message()
        self._publisher.publish(message)
        self._status.set(
            'Publishing: roll={:.2f} pitch={:.2f} yaw={:.2f} throttle={:.2f} deadman={}'.format(
                message.axes[0], message.axes[1], message.axes[2], message.axes[3], message.buttons[4]
            )
        )

    def _reset(self) -> None:
        self._roll.set(0.0)
        self._pitch.set(0.0)
        self._yaw.set(0.0)
        self._throttle.set(-1.0)
        self._deadman.set(0)
        self._publish()

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