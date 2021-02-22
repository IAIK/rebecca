#!/usr/bin/env python3
# Copyright IAIK TU Graz.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

import logging

logger = logging.getLogger()
handler = logging.FileHandler('tmp/log.txt')
formatter = logging.Formatter(
				'%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
