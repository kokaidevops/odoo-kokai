import logging
from odoo import http, models, fields, api, exceptions, _
from zk import ZK, const

_logger = logging.getLogger(__name__)

class DeviceUsers():
    def get_users(devices):
        all_users = []
        all_users.clear()
        for device in devices:
            with ConnectToDevice(device.ip_address, device.port, device.device_password) as conn:
                users = conn.get_users()
                all_users.extend(users)
                added = []
                added.clear()
                unique_data = []
                unique_data.clear()
                for user in all_users:
                    if int(user.user_id) not in added:
                        added.append(int(user.user_id))
                        added.sort()
                        unique_data.append(user)
        return unique_data

    def get_attendance(device):
        with ConnectToDevice(device.ip_address, device.port, device.device_password) as conn:
            attendances = conn.get_attendance()
            device_attendance = [[x.user_id, x.timestamp, x.punch, device.id] for x in attendances]
        return device_attendance

    def outputresult(user_punches):
        user_clock = []
        user_clock.clear()
        user_attendance = []
        user_attendance.clear()
        initial_number = 1

        for clock in user_punches:
            if clock[2] == initial_number:
                initial_number = clock[2]
                pass
            else:
                user_clock.append(clock)
                initial_number = clock[2]
        if len(user_clock) != 0 and user_clock[-1][2] == 0:
            del (user_clock[-1])
        user_attendance = [[i[0], i[1], j[1]] for i, j in zip(user_clock[::2], user_clock[1::2])]
        return user_attendance


class ConnectToDevice(object):
    def __init__(self, ip_address, port, device_password):
        try:
            zk = ZK(ip_address, port,timeout = 10, password=device_password, force_udp=False, ommit_ping=True)
            conn = zk.connect()
        except Exception as e:
            raise exceptions.Warning(e)
        conn.disable_device()
        self.conn = conn

    def __enter__(self):
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.enable_device()


class X100CDriver(http.Controller):
    @http.route("/hw_proxy/load_attendance_data", type="http", auth="none", cors="*")
    def load_attendance_data(self):
        conn = None
        zk = ZK('192.168.1.3', port=4370, timeout=5, password=0, force_udp=False, ommit_ping=True)
        try:
            conn = zk.connect()
            conn.disable_device()
            
            users = conn.get_users()
            for user in users:
                _logger.info('+ UID #{}'.format(user.uid))
                _logger.info('  Name       : {}'.format(user.name))
                _logger.info('  User  ID   : {}'.format(user.user_id))

            conn.enable_device()
        except Exception as e:
            _logger.info("Process terminate : {}".format(e))
        finally:
            if conn:
                conn.disconnect()