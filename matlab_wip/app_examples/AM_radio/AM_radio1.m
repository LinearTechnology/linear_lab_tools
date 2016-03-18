%The two predominant stations are at 680 and 850kHz as indicated by a 
%conventional spectrum analyzer.
%Sampled at 1.515MHz, the 680kHz(-71dBm) is within Nyquist. 
%The 850kHz(-80dBm) station aliases to 665kHz which is only 
%15kHz away...this stresses the receiver selectivity. The AM_radio1.m 
%can distinguish clearly between the two.
%Try lo_frequencies of 666000 and 686000 to hear the two different stations.

 bits_DAC = 16;
 bits_ADC = 16;
 seconds=10;
 fsamp_DAC = 2^16;
 fsamp_ADC = 1.515e6;

 %lo_frequency = 666000;
 %lo_frequency = 686000;
 
 lo_frequency = 686000; 
 
%create sample tone to test PC audio DAC 
% tone_frequency = 1000;
% i=1:fsamp_DAC*seconds;
% tone=sin(2*pi*tone_frequency*i/fsamp_DAC);
% soundsc(tone,fsamp_DAC,bits_DAC);

%get ADC samples for "seconds" duration
 num_samples = seconds*fsamp_ADC;
 %[data] =  get_data_2320_CMOS_8lanes_cont_run(num_samples);

 %assume radio channel is on ADC channel 1
%RF = data(:,1)';

load('C:\shared\AM_radio\1_minute_RF_recording\RF.mat', 'RF');

% Implement a pre-selection RF filter to increase receiver selectivity
%*******************************************************************
filt_size=2^8;
f_filt = lo_frequency;
f_samp = fsamp_ADC;
bpf_BW = 1000; %hz
%i=1:2^20;
filt_center = (f_filt/(f_samp))*filt_size;
bin_width = f_samp/(filt_size/2);
filt=zeros(1,filt_size);
filt(round(filt_center-(bpf_BW/2)/bin_width): round(filt_center+(bpf_BW/2)/bin_width))=1;
%plot(filt)
filt(filt_size/2+1:filt_size)=fliplr(filt(1:filt_size/2));
%plot(filt)
filt_cnv=real(fft(filt));
%plot(filt_cnv)
%sig_in(i)=sin(2*pi*i*1.5e6/(670e3));
RF_filtered=conv(RF,filt_cnv,'valid');
%plot((abs(real(fft(RF_filtered)))));
%*******************************************************************

%free memory for unused ADC channels
clear data;


%create a local oscillator to mix selected frequency to DC
LO = sin(2*pi*lo_frequency*(1:length(RF_filtered))/fsamp_ADC);

%downconvert selected channel with LO and apply AM detector 
baseband = abs(LO .* RF_filtered);
clear LO;
plot((abs(real(fft(baseband)))));
%plot(baseband)

%integrate and dump baseband to decimate to audio DAC frequency
decimation_factor = fsamp_ADC/fsamp_DAC;

decimated_baseband = zeros(1,round(length(baseband)/decimation_factor)+1);

for decimation_index = 1:length(decimated_baseband)
      decimated_baseband( decimation_index ) = sum( baseband(min(round((decimation_index-1)*decimation_factor)+1,length(baseband))) : baseband(min(length(baseband),round(decimation_index * decimation_factor))) );
end
%plot((decimated_baseband));
%soundsc(decimated_baseband,fsamp_DAC,bits_DAC);

decimated_baseband_filtered = zeros(1,length(decimated_baseband));
decimated_baseband_filtered(1) = decimated_baseband(1);

%apply a simple low pass filter to baseband
filter_coeff = 0.05;
for decimation_index = 2:length(decimated_baseband)
    decimated_baseband_filtered(decimation_index) = (1-filter_coeff) .* decimated_baseband_filtered(decimation_index-1)+ filter_coeff .* decimated_baseband( decimation_index );
end

%plot((abs(real(fft(decimated_baseband_filtered)))));

clear decimated_baseband;
%plot((decimated_baseband_filtered));

%send audio to the PC sound card 
soundsc(decimated_baseband_filtered,fsamp_DAC,bits_DAC);