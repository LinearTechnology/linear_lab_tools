function [maskA, maskB] = InteractiveMask(titleStr, data, nMasks, defaultMaskA, defaultMaskB)
   if ~exist('nMasks', 'var') || isempty(nMasks); nMasks = 1; end
   if ~exist('defaultMaskA', 'var') || isempty(defaultMaskA) 
       defaultMaskA = zeros(size(data));
   end
   if ~exist('defaultMaskB', 'var') || isempty(defaultMaskA) 
       defaultMaskB = [];
   end
   handles = InitMask(titleStr, data, nMasks, defaultMaskA, defaultMaskB);
   uiwait(handles.figure);
   if ishandle(handles.figure)
       userData = get(handles.figure, 'UserData');
       close(handles.figure);
       maskA = userData.maskA;
       maskB = userData.maskB;
   else
       maskA = defaultMaskA;
       maskB = defaultMaskB;
   end
end

function handles = InitMask(titleStr, data, nMasks, defaultMaskA, defaultMaskB)
    if nMasks == 1 && ~isempty(defaultMaskB)
        autoMask = defaultMaskB;
        defaultMaskB = [];
    else
        autoMask = [];
    end
    if nMasks == 2 && isempty(defaultMaskB)
        defaultMaskB = zeros(size(data));
    end
    handles.figure = figure;
    handles.axis = axes('Units', 'pixels');
    set(handles.figure, 'Units', 'pixels');
    handles.modeGroup = uibuttongroup(handles.figure, 'Units', 'pixels');
    handles.setRadio = uicontrol(handles.modeGroup, 'Style', 'radioButton', 'String', 'Set', ...
        'Units', 'pixels');
    handles.clearRadio = uicontrol(handles.modeGroup, 'Style', 'radioButton', 'String', 'Clear', ...
        'Units', 'pixels');
    handles.resetButton = uicontrol(handles.figure, 'Style', 'pushButton', 'String', 'Reset', ...
        'Units', 'pixels');
    handles.doneButton = uicontrol(handles.figure, 'Style', 'pushButton', 'String', 'Done', ...
        'Units', 'pixels');
    if isempty(autoMask)
        handles.autoButton = -1;
    else
        handles.autoButton = uicontrol(handles.figure, 'Style', 'pushButton', 'String', 'Auto', ...
            'Units', 'pixels');
    end
    if nMasks == 2
        handles.maskGroup = uibuttongroup('Units', 'Pixels');
        handles.maskARadio = uicontrol(handles.maskGroup, 'Style', 'radioButton', 'String', 'Mask A', ...
            'Units', 'pixels');
        handles.maskBRadio = uicontrol(handles.maskGroup, 'Style', 'radioButton', 'String', 'Mask B', ...
            'Units', 'pixels');
        if isempty(defaultMaskB)
            defaultMaskB = false(size(defaultMaskA));
        end
    else
        handles.maskGroup = -1;
        handles.maskARadio = -1;
        handles.maskBRadio = -1;
    end
    InitialSize(handles);
    PlotWithMasks(titleStr, data, defaultMaskA, defaultMaskB);
    
    userData.title = titleStr;
    userData.data = data;
    userData.defaultMaskA = defaultMaskA;
    userData.defaultMaskB = defaultMaskB;
    userData.autoMask = autoMask;
    userData.maskA = defaultMaskA;
    userData.maskB = defaultMaskB;
    userData.currentMask = 1;
    userData.xPos = [];
    userData.isClear = false;
    userData.patch = patch([0, 0, 0, 0], [0, 0, 0, 0], 'c', 'FaceAlpha', .3, 'EdgeAlpha', 0);
    set(handles.figure, 'UserData', userData);
        set(handles.figure, 'ResizeFcn', @(o,e) Resize(handles));
    set(handles.figure, 'WindowButtonDownFcn', @(o,e) OnButtonDown(handles));
    set(handles.figure, 'WindowButtonMotionFcn', @(o,e) OnMouseMove(handles));
    set(handles.figure, 'WindowButtonUpFcn', @(o,e) OnButtonUp(handles));
    set(handles.doneButton, 'Callback', @(o, e) uiresume(handles.figure));
    set(handles.resetButton, 'Callback', @(o, e) OnReset(handles));
    if ~isempty(autoMask)
        set(handles.autoButton, 'Callback', @(o, e) OnAutoMask(handles));
    end
    radioCallback = 'SelectionChangedFcn';
    if verLessThan('matlab', '8.4')
        radioCallback = 'SelectionChangeFcn';
    end
    set(handles.modeGroup, radioCallback, @(o, e) OnModeChange(handles, e));
    if nMasks == 2
        set(handles.maskGroup, radioCallback, @(o, e) OnMaskChange(handles, e));
    end
end

function InitialSize(handles)
    modeRadioPos = get(handles.clearRadio, 'Position');
    buttonPos = get(handles.resetButton, 'Position');
    set(handles.resetButton, 'Position', [10, 10, buttonPos(3), buttonPos(4)]);
    set(handles.setRadio, 'Position', [5, 10 + modeRadioPos(4), modeRadioPos(3), modeRadioPos(4)]);
    set(handles.clearRadio, 'Position', [5, 5, modeRadioPos(3), modeRadioPos(4)]);
    set(handles.modeGroup, 'Position', [10, 15 + buttonPos(4), 10 + modeRadioPos(3), 15 + 2 * modeRadioPos(4)]);
    if handles.autoButton ~= -1
        autoPos = get(handles.autoButton, 'Position');
        set(handles.autoButton, 'Position', [35 + modeRadioPos(3), 10, autoPos(3), autoPos(4)]);
    end
    if handles.maskGroup ~= -1
        maskRadioPos = get(handles.maskARadio, 'Position');
        set(handles.maskARadio, 'Position', [5, 10 + maskRadioPos(4), maskRadioPos(3), maskRadioPos(4)]);
        set(handles.maskBRadio, 'Position', [5, 5, maskRadioPos(3), maskRadioPos(4)]);
        set(handles.maskGroup, 'Position', [35 + modeRadioPos(3), 15 + buttonPos(4), ...
            10 + maskRadioPos(3), 15 + 2 * maskRadioPos(4)]);
    end
    Resize(handles)
end
    
function Resize(handles)
    figurePos = get(handles.figure, 'Position');
    buttonPos = get(handles.resetButton, 'Position');
    modeRadioPos = get(handles.clearRadio, 'Position');
    y = 60 + buttonPos(4) + 2 * modeRadioPos(4);
    set(handles.axis, 'Position', [30, y, figurePos(3) - 50, figurePos(4) - y - 30]);
    set(handles.doneButton, 'Position', [figurePos(3) - buttonPos(3) - 10, 10, ...
    buttonPos(3), buttonPos(4)]);
end

function [dataCells, starts] = SplitData(data, mask)
    indices = find(mask);
    if isempty(indices)
        dataCells = [];
        starts = [];
        return;
    end
    starts = indices(2:end);
    starts = [indices(1), starts(indices(2:end) - indices(1:(end-1)) > 1)];
    nStarts = length(starts);
    dataCells = cell(1, nStarts);
    for i = 1:(nStarts - 1)
        indices = starts(i) + find(mask(starts(i):(starts(i+1)-1))) - 1;
        if indices(end) ~= length(data)
            indices = [indices, indices(end) + 1]; %#ok only sometime grows and we don't know the size
        end
        dataCells{i} = data(indices);
    end
    indices = starts(end) + find(mask(starts(end):end)) - 1;
    if indices(end) ~= length(data)
        indices = [indices, indices(end) + 1];
    end
    dataCells{nStarts} = data(indices);
end

function PlotWithMasks(titleStr, data, maskA, maskB)   
    % A mask
    [aData, aStarts] = SplitData(data, maskA);
    
    if ~isempty(maskB)
        % B mask not counting any A mask
        [bData, bStarts] = SplitData(data, maskB & (~maskA));
        % no mask
        [uData, uStarts] = SplitData(data, ~(maskA | maskB));
    else
        % empty B mask
        bData = [];
        bStarts = [];
        % no mask
        [uData, uStarts] = SplitData(data, ~maskA);
    end
    
    starts = [uStarts, aStarts, bStarts];
    fusedData = [uData, aData, bData];
    colors = [repmat('k', 1, length(uStarts)), repmat('c', 1, length(aStarts)), ...
        repmat('m', 1, length(bStarts))];
    [starts, idx] = sort(starts);
    fusedData = fusedData(idx);
    colors = colors(idx);
    for i = 1:length(starts)
        n = length(fusedData{i});
        plot(starts(i) - 1 + (1:n), fusedData{i}, colors(i));
        hold on
    end
    hold off
    
    lims = axis;
    n = length(data);
    dx = n / 20;
    axis([-dx, n + dx, lims(3), lims(4)]);
    title(titleStr);
end

function OnButtonDown(handles)
userData = get(handles.figure, 'UserData');
point = get(handles.axis,'CurrentPoint');
userData.xPos = point(1);
userData.mouseDown = true;
set(handles.figure, 'UserData', userData);
end

function OnMouseMove(handles)
    userData = get(handles.figure, 'UserData');
    if ~isempty(userData.xPos)
        xLim = get(handles.axis, 'XLim');
        yLim = get(handles.axis, 'YLim');
        point = get(handles.axis, 'CurrentPoint');
        newPos = max(xLim(1), min(xLim(2), point(1)));
        if userData.isClear
            if userData.currentMask == 1
                color = 'b';
            else
                color = 'r';
            end
        else
            if userData.currentMask == 1
                color = 'c';
            else
                color = 'm';
            end
        end
        set(userData.patch, 'XData', [userData.xPos, userData.xPos, newPos, newPos], ...
            'YData', [yLim(1), yLim(2), yLim(2), yLim(1)], 'FaceColor', color);
    end
end

function OnButtonUp(handles)
    userData = get(handles.figure, 'UserData');
    if ~isempty(userData.xPos)
        point = get(handles.axis, 'CurrentPoint');
        xLim = get(handles.axis, 'XLim');
        newPos = max(xLim(1), min(xLim(2), point(1)));
        n = length(userData.defaultMaskA);
        newMask = false(1, n);
        indices = 1:n;
        newMask(indices >= userData.xPos & indices <= newPos) = true;
        if userData.isClear
            if userData.currentMask == 1
                userData.maskA = userData.maskA & (~newMask);
            else
                userData.maskB = userData.maskB & (~newMask);
            end
        else
            if userData.currentMask == 1
                userData.maskA = userData.maskA | newMask;
            else
                userData.maskB = userData.maskB | newMask;
            end
        end
        
        PlotWithMasks(userData.title, userData.data, userData.maskA, userData.maskB);
        
        userData.xPos = [];
    end
    userData.patch = patch([0, 0, 0, 0], [0, 0, 0, 0], 'c', 'FaceAlpha', .3, 'EdgeAlpha', 0);
    set(handles.figure, 'UserData', userData);
end

function OnModeChange(handles, e)
    userData = get(handles.figure, 'UserData');
    userData.isClear = strcmp(get(e.NewValue, 'String'), 'Clear');
    set(handles.figure, 'UserData', userData);
end

function OnMaskChange(handles, e)
    userData = get(handles.figure, 'UserData');
    if strcmp(get(e.NewValue, 'String'), 'Mask A')
        userData.currentMask = 1;
    else
        userData.currentMask = 2;
    end
    set(handles.figure, 'UserData', userData);
end

function OnReset(handles)
    userData = get(handles.figure, 'UserData');
    userData.maskA = userData.defaultMaskA;
    userData.maskB = userData.defaultMaskB;
    PlotWithMasks(userData.title, userData.data, userData.maskA, userData.maskB);
    userData.patch = patch([0, 0, 0, 0], [0, 0, 0, 0], 'c', 'FaceAlpha', .3, 'EdgeAlpha', 0);
    set(handles.figure, 'UserData', userData);
end

function OnAutoMask(handles)
    userData = get(handles.figure, 'UserData');
    userData.maskA = userData.autoMask;
    PlotWithMasks(userData.title, userData.data, userData.maskA, userData.maskB);
    userData.patch = patch([0, 0, 0, 0], [0, 0, 0, 0], 'c', 'FaceAlpha', .3, 'EdgeAlpha', 0);
    set(handles.figure, 'UserData', userData);
end
        