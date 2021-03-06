#!/usr/bin/env python

#
# Copyright 2006, 2007, 2008 Free Software Foundation, Inc.
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
# 

import math
from numpy import fft
from gnuradio import gr

import digital_swig
from ofdm_sync_pn import ofdm_sync_pn
from ofdm_sync_fixed import ofdm_sync_fixed
from ofdm_sync_pnac import ofdm_sync_pnac
from ofdm_sync_ml import ofdm_sync_ml

class ofdm_receiver(gr.hier_block2):
    """
    Performs receiver synchronization on OFDM symbols.

    The receiver performs channel filtering as well as symbol, frequency, and phase synchronization.
    The synchronization routines are available in three flavors: preamble correlator (Schmidl and Cox),
    modifid preamble correlator with autocorrelation (not yet working), and cyclic prefix correlator
    (Van de Beeks).
    """

    def __init__(self, fft_length, cp_length, occupied_tones, snr, ks, threshold, options, logging=False):
        """
	Hierarchical block for receiving OFDM symbols.

	The input is the complex modulated signal at baseband.
        Synchronized packets are sent back to the demodulator.

        @param fft_length: total number of subcarriers
        @type  fft_length: int
        @param cp_length: length of cyclic prefix as specified in subcarriers (<= fft_length)
        @type  cp_length: int
        @param occupied_tones: number of subcarriers used for data
        @type  occupied_tones: int
        @param snr: estimated signal to noise ratio used to guide cyclic prefix synchronizer
        @type  snr: float
        @param ks: known symbols used as preambles to each packet
        @type  ks: list of lists
        @param logging: turn file logging on or off
        @type  logging: bool
	"""

	gr.hier_block2.__init__(self, "ofdm_receiver",
				gr.io_signature(1, 1, gr.sizeof_gr_complex), # Input signature
                                #gr.io_signature2(2, 2, gr.sizeof_gr_complex*occupied_tones, gr.sizeof_char)) # Output signature apurv--
				gr.io_signature3(3, 3, gr.sizeof_gr_complex*occupied_tones, gr.sizeof_char, gr.sizeof_gr_complex*occupied_tones))	# apurv++, goes into frame sink for hestimates
        			#gr.io_signature4(4, 4, gr.sizeof_gr_complex*occupied_tones, gr.sizeof_char, gr.sizeof_gr_complex*occupied_tones, gr.sizeof_gr_complex*fft_length))     # apurv++, goes into frame sink for hestimates

        bw = (float(occupied_tones) / float(fft_length)) / 2.0
        tb = bw*0.08
        chan_coeffs = gr.firdes.low_pass (1.0,                     # gain
                                          1.0,                     # sampling rate
                                          bw+tb,                   # midpoint of trans. band
                                          tb,                      # width of trans. band
                                          gr.firdes.WIN_HAMMING)   # filter type
        self.chan_filt = gr.fft_filter_ccc(1, chan_coeffs)
        
        win = [1 for i in range(fft_length)]

        zeros_on_left = int(math.ceil((fft_length - occupied_tones)/2.0))
        ks0 = fft_length*[0,]
        ks0[zeros_on_left : zeros_on_left + occupied_tones] = ks[0]
        
	

        ks0 = fft.ifftshift(ks0)
        ks0time = fft.ifft(ks0)
        # ADD SCALING FACTOR
        ks0time = ks0time.tolist()

        nco_sensitivity = -2.0/fft_length                             # correct for fine frequency
	self.ofdm_sync = ofdm_sync_pn(fft_length, cp_length, ks0time, threshold, options.threshold_type, options.threshold_gap, logging)  # apurv++

        # Set up blocks

        self.nco = gr.frequency_modulator_fc(nco_sensitivity)         # generate a signal proportional to frequency error of sync block
        self.sigmix = gr.multiply_cc()				     
        self.sampler = digital_swig.ofdm_sampler(fft_length, fft_length+cp_length, len(ks)+1, 100)	# 1 for the extra preamble which ofdm_rx doesn't know about (check frame_sink)
        self.fft_demod = gr.fft_vcc(fft_length, True, win, True)
        self.ofdm_frame_acq = digital_swig.ofdm_frame_acquisition(occupied_tones, fft_length,
                                                        cp_length, ks)

        if options.verbose:
            self._print_verbage(options)

	# apurv++ modified to allow collected time domain data to artifically pass through the rx chain #
		
	# to replay the input manually, use this #
	#self.connect(self, gr.null_sink(gr.sizeof_gr_complex))
	#self.connect(gr.file_source(gr.sizeof_gr_complex, "input.dat"), self.chan_filt)		

	############# input -> chan_filt ##############
	self.connect(self, self.chan_filt)
	
	use_chan_filt = options.use_chan_filt
	correct_freq_offset = 0

	if use_chan_filt == 1:
 	    ##### chan_filt -> SYNC, chan_filt -> SIGMIX ####
	    self.connect(self.chan_filt, self.ofdm_sync)
	    if correct_freq_offset == 1:
		# enable if frequency offset correction is required #
       	    	self.connect(self.chan_filt, gr.delay(gr.sizeof_gr_complex, (fft_length)), (self.sigmix, 0))        # apurv++ follow freq offset
	    else:
		self.connect(self.chan_filt, (self.sampler, 0))
		###self.connect(self.chan_filt, gr.delay(gr.sizeof_gr_complex, (fft_length)), (self.sampler, 0))		## extra delay

	    #self.connect(self.chan_filt, gr.file_sink(gr.sizeof_gr_complex, "ofdm_receiver-chan_filt_c.dat"))
	elif use_chan_filt == 2: 
	    #### alternative: chan_filt-> NULL, file_source -> SYNC, file_source -> SIGMIX ####
	    self.connect(self.chan_filt, gr.null_sink(gr.sizeof_gr_complex))
	    if correct_freq_offset == 1:
	        self.connect(gr.file_source(gr.sizeof_gr_complex, "chan_filt.dat"), self.ofdm_sync)
	   	self.connect(gr.file_source(gr.sizeof_gr_complex, "chan_filt.dat"), gr.delay(gr.sizeof_gr_complex, (fft_length)), (self.sigmix, 0))
	    else:
		self.connect(gr.file_source(gr.sizeof_gr_complex, "chan_filt.dat"), self.ofdm_sync)
		self.connect(gr.file_source(gr.sizeof_gr_complex, "chan_filt.dat"), (self.sampler, 0))
	else:
	    # chan_filt->NULL #
	    self.connect(self.chan_filt, gr.null_sink(gr.sizeof_gr_complex))
	
	method = options.method
	if method == -1:
	    ################## for offline analysis, dump sampler input till the frame_sink, using io_signature4 #################
	    if correct_freq_offset == 1:
		# enable if frequency offset correction is required #
            	self.connect((self.ofdm_sync,0), self.nco, (self.sigmix,1))   					# freq offset (0'ed :/)
	        self.connect(self.sigmix, (self.sampler,0))                   					# corrected output (0'ed FF)
		self.connect((self.ofdm_sync,1), gr.delay(gr.sizeof_char, fft_length), (self.sampler, 1))           # timing signal

	    else:
		# disable frequency offset correction completely #
		self.connect((self.ofdm_sync,0), gr.null_sink(gr.sizeof_float))
		self.connect((self.ofdm_sync,1), (self.sampler, 1))           # timing signal,	

		#self.connect((self.ofdm_sync,0), (self.sampler, 2))						##added
		##self.connect((self.ofdm_sync,1), gr.delay(gr.sizeof_char, fft_length+cp_length), (self.sampler, 1))           # timing signal, ##extra delay


	    # route received time domain to sink (all-the-way) for offline analysis #
	    self.connect((self.sampler, 0), (self.ofdm_frame_acq, 2))
	    #self.connect((self.sampler, 1), gr.file_sink(gr.sizeof_char*fft_length, "sampler_timing.dat"))

	elif method == 0:
            # NORMAL functioning #
    	    if correct_freq_offset == 1:
	        self.connect((self.ofdm_sync,0), self.nco, (self.sigmix,1))   # use sync freq. offset output to derotate input signal
	    	self.connect(self.sigmix, (self.sampler,0))                   # sample off timing signal detected in sync alg
	    	self.connect((self.ofdm_sync,1), gr.delay(gr.sizeof_char, fft_length), (self.sampler, 1))		# delay?
	    else:
		self.connect((self.ofdm_sync,1), (self.sampler, 1))

	    #self.connect((self.sampler, 2), (self.ofdm_frame_acq, 2))	
	#######################################################################

	use_default = options.use_default
        if use_default == 0:		#(set method == 0)
		# sampler-> NULL, replay trace->fft_demod, ofdm_frame_acq (time domain) #
	    #self.connect((self.sampler, 0), gr.null_sink(gr.sizeof_gr_complex*fft_length))
	    #self.connect((self.sampler, 1), gr.null_sink(gr.sizeof_char*fft_length))
	
            self.connect(gr.file_source(gr.sizeof_gr_complex*fft_length, "symbols_src.dat"), self.fft_demod)
            self.connect(gr.file_source(gr.sizeof_char*fft_length, "timing_src.dat"), (self.ofdm_frame_acq,1))
	    self.connect(self.fft_demod, (self.ofdm_frame_acq,0))
	elif use_default == 1:		#(set method == -1)
		# normal functioning #
            self.connect((self.sampler,0), self.fft_demod)                # send derotated sampled signal to FFT
            self.connect((self.sampler,1), (self.ofdm_frame_acq,1))       # send timing signal to signal frame start
	    self.connect(self.fft_demod, (self.ofdm_frame_acq,0))
        elif use_default == 2:
	       # replay directly to ofdm_frame_acq (frequency domain) #
            self.connect(gr.file_source(gr.sizeof_gr_complex*fft_length, "symbols_src.dat"), (self.ofdm_frame_acq,0))
            self.connect(gr.file_source(gr.sizeof_char*fft_length, "timing_src.dat"), (self.ofdm_frame_acq,1))
	
	########################### some logging start ##############################
	#self.connect((self.ofdm_sync,1), gr.delay(gr.sizeof_char, fft_length), gr.file_sink(gr.sizeof_char, "ofdm_sync_pn-peaks_b.dat"))
        #self.connect((self.sampler, 0), gr.file_sink(gr.sizeof_gr_complex*fft_length, "ofdm_receiver-sampler_c.dat"))
       	#self.connect((self.sampler, 1), gr.file_sink(gr.sizeof_char*fft_length, "ofdm_timing_sampler_c.dat"))
	############################ some logging end ###############################

        self.connect((self.ofdm_frame_acq,0), (self,0))               # finished with fine/coarse freq correction,
        self.connect((self.ofdm_frame_acq,1), (self,1))               # frame and symbol timing, and equalization
        self.connect((self.ofdm_frame_acq,2), (self,2))               # equalizer: hestimates 

	#self.connect((self.ofdm_frame_acq,3), (self,3))           # ref sampler above

	# apurv++ ends #

	#self.connect(self.ofdm_frame_acq, gr.file_sink(gr.sizeof_gr_complex*occupied_tones, "ofdm_receiver-frame_acq_c.dat"))
	#self.connect((self.ofdm_frame_acq,1), gr.file_sink(1, "ofdm_receiver-found_corr_b.dat"))


	# apurv++ log the fine frequency offset corrected symbols #
	#self.connect((self.ofdm_frame_acq, 1), gr.file_sink(gr.sizeof_char, "ofdm_timing_frame_acq_c.dat"))
        #self.connect((self.ofdm_frame_acq, 2), gr.file_sink(gr.sizeof_gr_complex*occupied_tones, "ofdm_hestimates_c.dat"))
	#self.connect(self.fft_demod, gr.file_sink(gr.sizeof_gr_complex*fft_length, "ofdm_receiver-fft_out_c.dat"))
	#self.connect(self.chan_filt, gr.file_sink(gr.sizeof_gr_complex, "ofdm_receiver-chan_filt_c.dat"))
	#self.connect(self, gr.file_sink(gr.sizeof_gr_complex, "ofdm_input_c.dat"))
	# apurv++ end #

        if logging:
            self.connect(self.chan_filt, gr.file_sink(gr.sizeof_gr_complex, "ofdm_receiver-chan_filt_c.dat"))
            self.connect(self.fft_demod, gr.file_sink(gr.sizeof_gr_complex*fft_length, "ofdm_receiver-fft_out_c.dat"))
            self.connect(self.ofdm_frame_acq,
                         gr.file_sink(gr.sizeof_gr_complex*occupied_tones, "ofdm_receiver-frame_acq_c.dat"))
            self.connect((self.ofdm_frame_acq,1), gr.file_sink(1, "ofdm_receiver-found_corr_b.dat"))
            self.connect(self.sampler, gr.file_sink(gr.sizeof_gr_complex*fft_length, "ofdm_receiver-sampler_c.dat"))
            #self.connect(self.sigmix, gr.file_sink(gr.sizeof_gr_complex, "ofdm_receiver-sigmix_c.dat"))
            self.connect(self.nco, gr.file_sink(gr.sizeof_gr_complex, "ofdm_receiver-nco_c.dat"))

    def _print_verbage(self, options):
        """
        Prints information about the OFDM receiver specific options
        """
	print "\n--------------------------------------------------"
        print "OFDM Receiver flags:"
        print "use_chan_filt: %3d"    % (options.use_chan_filt)
        print "method:      %3d"   % (options.method)
        print "use_default:  %3d"   % (options.use_default)
	print "rx_manual:       %3d"   % (options.rx_manual)
	print "----------------------------------------------------\n"

