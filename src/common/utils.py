#!/usr/bin/env python

# utils.py
#
# Copyright (C) 2014 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU General Public License v2
#
#
# Utility functions
#
# This is a mixed collection of functions which can be
# used on all three platforms. Anything else, must be
# placed in the appropriate platform folder.


import os
import sys
import time
import shutil
import psutil
import signal
import subprocess
from urllib2 import urlopen
from PyQt4 import QtCore

from src.common.paths import temp_path


# Conversion constants
# technically, gigabyte=1000^3 and gibibyte=1024^3 - here, the difference matters
BYTES_IN_MEGABYTE = 1000000
BYTES_IN_GIGABYTE = 1000000000


# The URL used to download information about the lastest OS release
LATEST_OS_INFO_URL = 'http://downloads.kano.me/public/latest.json'


def debugger(text):
    # if we are running from a PyInstaller bundle, print debug to file
    if getattr(sys, 'frozen', False):
        with open(os.path.join(temp_path, 'debug.txt'), "a") as debug_file:
            debug_file.write(text + '\n')
    # otherwise, print debug to stdout
    else:
        print text


def run_cmd(cmd):
    process = subprocess.Popen(cmd, shell=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               preexec_fn=restore_signals)

    stdout, stderr = process.communicate()
    return_code = process.returncode
    return stdout, stderr, return_code


def restore_signals():
        signals = ('SIGPIPE', 'SIGXFZ', 'SIGXFSZ')
        for sig in signals:
            if hasattr(signal, sig):
                signal.signal(getattr(signal, sig), signal.SIG_DFL)


def run_cmd_no_pipe(cmd):
    # used on Windows as there is no support for 'preexec_fn'
    # all handles (in, out, err) need to be set due to PyInstaller bundling
    process = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = process.communicate()
    return_code = process.returncode
    return stdout, stderr, return_code


def stop_child_processes():
    try:
        parent = psutil.Process(os.getpid())
        processes_left = True

        while processes_left:
            processes_left = False

            for child in parent.children(recursive=True):
                if child.name() != 'conhost.exe':
                    debugger('Killing {}'.format(child.name()))
                    child.kill()
                    processes_left = True

            time.sleep(2)
    except:
        debugger('[ERROR] Killing child processes failed')


def delete_dir(directory):
    try:
        if os.path.exists(directory):
            shutil.rmtree(directory)
        return True
    except:
        debugger('[ERROR] Deleting directory {} failed'.format(directory))
        return False


def make_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def read_file_contents(path):
    if os.path.exists(path):
        with open(path) as infile:
            content = infile.readlines()
            lines = [line.strip() for line in content]
            return '\n'.join(lines)


def write_file_contents(data, path):
    with open(path, 'w') as outfile:
        outfile.write(data)


def is_internet():
    url_list = ['https://google.com',
                'https://twitter.com',
                'https://facebook.com',
                'https://youtube.com']
    for url in url_list:
        try:
            urlopen(url, timeout=1)
            return True
        except:
            pass
    return False


def load_css_for_widget(widget, css_path, res_path=''):
    '''
    This method is used to set CSS styling for a given
    widget from a given CSS file.

    If a resource path is given, it will attempt to replace
    {res_path} in the CSS with that path.

    NOTE: It assumes only one {res_path} string will be on a single line.
    '''

    css = QtCore.QFile(css_path)
    css.open(QtCore.QIODevice.ReadOnly)
    if css.isOpen():
        style_sheet = str(QtCore.QVariant(css.readAll()).toString())

        if res_path:
            style_sheet_to_format = style_sheet
            style_sheet = ''

            for line in style_sheet_to_format.splitlines():
                try:
                    line = line.format(res_path=os.path.join(res_path, '').replace('\\', '/'))
                except ValueError:
                    pass
                except Exception:
                    debugger('[ERROR] Formatting CSS file {} failed on line "{}"'
                             .format(css_path, line))

                style_sheet += line + '\n'

        widget.setStyleSheet(style_sheet)
    css.close()


def calculate_eta(progress, total, speed):
    '''
    This function is used by the burning process to calculate when
    it is expected to finish based on current progress, the total
    needed, and the speed - e.g. 450 MB of 1000 MB at 50 MB/s.

    NOTE: Units must match.
    '''

    eta_seconds = float(total - progress) / (speed + 1)

    hours = int(eta_seconds / 3600)
    minutes = int(eta_seconds / 60 - hours * 60)
    seconds = int(eta_seconds % 60)

    if hours:
        return '{} hours, {} minutes, {} seconds'.format(hours, minutes, seconds)
    elif minutes:
        return '{} minutes, {} seconds'.format(minutes, seconds)
    else:
        return '{} seconds'.format(seconds)
