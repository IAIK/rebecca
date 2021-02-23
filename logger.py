#!/usr/bin/env python3
# Copyright IAIK TU Graz.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

import logging
import os

# Make sure the work directory exists.
path = os.getcwd()
tmp_dir = path + '/tmp'
if not os.path.exists(tmp_dir):
	try:
		os.makedirs(tmp_dir)
	except OSError:
		print('ERR: cannot create dir ' + str(tmp_dir))
		exit()

logger = logging.getLogger()
handler = logging.FileHandler('tmp/log.txt')
formatter = logging.Formatter(
				'%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
