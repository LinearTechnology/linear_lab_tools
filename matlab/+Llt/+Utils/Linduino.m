function ser = Linduino()
ser = [];
for port = 0:255
    s = serial(sprintf('COM%d', port), 'BaudRate', 115200);
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
    idStr = fgetl(s);
    if strcmp(idStr(21:25), 'DC590')
        ser = s;
        return;
    else 
        fclose(s);
        delete(s);
        clear(s);
    end
end
        