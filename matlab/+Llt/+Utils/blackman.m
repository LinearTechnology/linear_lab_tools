function window = blackman(size)

normalization = 1.968888;    
a0 = 0.35875;
a1 = 0.48829;
a2 = 0.14128;
a3 = 0.01168;
    
t1 = (0:(size-1)) / (size - 1.0);
t2 = 2 * t1;
t3 = 3 * t1;
t1 = t1 - floor(t1);
t2 = t2 - floor(t2);
t3 = t3 - floor(t3);

window = a0 - ...
         a1*cos(2*pi*t1) + ...
         a2*cos(2*pi*t2) - ...
         a3*cos(2*pi*t3);

window = window / normalization;
window = window(:);
