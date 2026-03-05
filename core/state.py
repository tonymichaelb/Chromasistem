"""Shared mutable state for Chromasistem.

Usage: import core.state as st
Then access/modify as st.variable_name.
"""

printer_serial = None

print_paused = False
print_stopped = False
print_paused_by_filament = False
printing_thread = None
printing_in_progress = False
g28_executed = False
g29_executed = False
pause_option_requested = 'keep_temp'
current_pause_state_job_id = None
_pause_mem_state = {
    'pos_x': None, 'pos_y': None, 'pos_z': None, 'pos_e': None,
    'target_nozzle': 0, 'target_bed': 0, 'option': 'keep_temp',
    'valid': False,
}

print_failure_detected = False
current_failure_message = None
current_failure_code = None
skip_requested = False
skip_object_id = None

_consecutive_cmd_failures = 0
CONSECUTIVE_FAILURES_THRESHOLD = 3

filament_status = {
    'has_filament': True,
    'sensor_enabled': True,
    'source': 'gpio',
    'last_check': None
}

gpio_live_updates_active = False
_gpio_poll_thread_started = False
_filament_last_check_idle_ts = 0.0
_filament_last_check_print_ts = 0.0

_temp_last_check_print_ts = 0.0
_temp_cache_print = {
    'bed': 0,
    'nozzle': 0,
    'target_bed': 0,
    'target_nozzle': 0,
}

current_brush = 0
