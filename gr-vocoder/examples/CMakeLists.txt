# Copyright 2011 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# GNU Radio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# GNU Radio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.

########################################################################
# Install Examples
########################################################################
include(GrPython)

GR_PYTHON_INSTALL(
    PROGRAMS
    alaw_audio_loopback.py
    codec2_audio_loopback.py
    cvsd_audio_loopback.py
    g721_audio_loopback.py
    g723_24_audio_loopback.py
    g723_40_audio_loopback.py
    gsm_audio_loopback.py
    ulaw_audio_loopback.py
    DESTINATION ${GR_PKG_DATA_DIR}/examples/vocoder
    COMPONENT "vocoder_examples"
)
