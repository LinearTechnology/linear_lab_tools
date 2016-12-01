function ser = linduino()
ser = [];
warning('off', 'MATLAB:serial:fgetl:unsuccessfulRead');
for port = 0:255
    s = serial(sprintf('COM%d', port), 'BaudRate', 115200, 'Timeout', 1); %#ok
    try
        fopen(s);
    catch
        delete(s);
        clear s;
        continue;
    end
    pause(2);
    fgetl(s);
    fprintf(s, 'i');
    id_str = fgetl(s);
    if strcmp(id_str(21:25), 'DC590')
        ser = s;
        fprintf('Port %d appears to be a DC590 or Linduino\n', port);
        warning('on', 'MATLAB:serial:fgetl:unsuccessfulRead');
        return;
    else 
        fclose(s);
        delete(s);
        clear s;
    end
end
fprintf('Did not find a DC590 or Linduino');
warning('on', 'MATLAB:serial:fgetl:unsuccessfulRead');
        