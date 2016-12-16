function [mask_a, mask_b] = interactive_mask(title_str, data, num_masks, default_mask_a, default_mask_b)
   if ~exist('num_masks', 'var') || isempty(num_masks); num_masks = 1; end
   if ~exist('default_mask_a', 'var') || isempty(default_mask_a) 
       default_mask_a = zeros(size(data));
   end
   if ~exist('default_mask_b', 'var') || isempty(default_mask_b) 
       default_mask_b = [];
   end
   handles = init_mask(title_str, data, num_masks, default_mask_a, default_mask_b);
   uiwait(handles.figure);
   if ishandle(handles.figure)
       user_data = get(handles.figure, 'UserData');
       close(handles.figure);
       mask_a = user_data.mask_a;
       mask_b = user_data.mask_b;
   else
       mask_a = default_mask_a;
       mask_b = default_mask_b;
   end
end

function handles = init_mask(title_str, data, num_masks, default_mask_a, default_mask_b)
    if num_masks == 1 && ~isempty(default_mask_b)
        auto_mask = default_mask_b;
        default_mask_b = [];
    else
        auto_mask = [];
    end
    if num_masks == 2 && isempty(default_mask_b)
        default_mask_b = zeros(size(data));
    end
    handles.figure = figure;
    handles.axis = axes('Units', 'pixels');
    set(handles.figure, 'Units', 'pixels');
    handles.mode_group = uibuttongroup(handles.figure, 'Units', 'pixels');
    handles.set_radio = uicontrol(handles.mode_group, 'Style', 'radioButton', 'String', 'Set', ...
        'Units', 'pixels');
    handles.clear_radio = uicontrol(handles.mode_group, 'Style', 'radioButton', 'String', 'Clear', ...
        'Units', 'pixels');
    handles.reset_button = uicontrol(handles.figure, 'Style', 'pushButton', 'String', 'Reset', ...
        'Units', 'pixels');
    handles.done_button = uicontrol(handles.figure, 'Style', 'pushButton', 'String', 'Done', ...
        'Units', 'pixels');
    if isempty(auto_mask)
        handles.auto_button = -1;
    else
        handles.auto_button = uicontrol(handles.figure, 'Style', 'pushButton', 'String', 'Auto', ...
            'Units', 'pixels');
    end
    if num_masks == 2
        handles.mask_group = uibuttongroup('Units', 'Pixels');
        handles.mask_a_radio = uicontrol(handles.mask_group, 'Style', 'radioButton', 'String', 'Mask A', ...
            'Units', 'pixels');
        handles.mask_b_radio = uicontrol(handles.mask_group, 'Style', 'radioButton', 'String', 'Mask B', ...
            'Units', 'pixels');
        if isempty(default_mask_b)
            default_mask_b = false(size(default_mask_a));
        end
    else
        handles.mask_group = -1;
        handles.mask_a_radio = -1;
        handles.mask_b_radio = -1;
    end
    initial_size(handles);
    plot_with_masks(title_str, data, default_mask_a, default_mask_b);
    
    user_data.title = title_str;
    user_data.data = data;
    user_data.default_mask_a = default_mask_a;
    user_data.default_mask_b = default_mask_b;
    user_data.auto_mask = auto_mask;
    user_data.mask_a = default_mask_a;
    user_data.mask_b = default_mask_b;
    user_data.current_mask = 1;
    user_data.x_pos = [];
    user_data.is_clear = false;
    user_data.patch = patch([0, 0, 0, 0], [0, 0, 0, 0], 'c', 'FaceAlpha', .3, 'EdgeAlpha', 0);
    set(handles.figure, 'UserData', user_data);
        set(handles.figure, 'ResizeFcn', @(o,e) resize(handles));
    set(handles.figure, 'WindowButtonDownFcn', @(o,e) on_button_down(handles));
    set(handles.figure, 'WindowButtonMotionFcn', @(o,e) on_mouth_move(handles));
    set(handles.figure, 'WindowButtonUpFcn', @(o,e) on_button_up(handles));
    set(handles.done_button, 'Callback', @(o, e) uiresume(handles.figure));
    set(handles.reset_button, 'Callback', @(o, e) on_reset(handles));
    if ~isempty(auto_mask)
        set(handles.auto_button, 'Callback', @(o, e) on_auto_mask(handles));
    end
    radio_callback = 'SelectionChangedFcn';
    if verLessThan('matlab', '8.4')
        radio_callback = 'SelectionChangeFcn';
    end
    set(handles.mode_group, radio_callback, @(o, e) on_mode_change(handles, e));
    if num_masks == 2
        set(handles.mask_group, radio_callback, @(o, e) on_mask_change(handles, e));
    end
end

function initial_size(handles)
    mode_radio_pos = get(handles.clear_radio, 'Position');
    button_pos = get(handles.reset_button, 'Position');
    set(handles.reset_button, 'Position', [10, 10, button_pos(3), button_pos(4)]);
    set(handles.set_radio, 'Position', [5, 10 + mode_radio_pos(4), mode_radio_pos(3), mode_radio_pos(4)]);
    set(handles.clear_radio, 'Position', [5, 5, mode_radio_pos(3), mode_radio_pos(4)]);
    set(handles.mode_group, 'Position', [10, 15 + button_pos(4), 10 + mode_radio_pos(3), 15 + 2 * mode_radio_pos(4)]);
    if handles.auto_button ~= -1
        auto_pos = get(handles.auto_button, 'Position');
        set(handles.auto_button, 'Position', [35 + mode_radio_pos(3), 10, auto_pos(3), auto_pos(4)]);
    end
    if handles.mask_group ~= -1
        mask_radio_pos = get(handles.mask_a_radio, 'Position');
        set(handles.mask_a_radio, 'Position', [5, 10 + mask_radio_pos(4), mask_radio_pos(3), mask_radio_pos(4)]);
        set(handles.mask_b_radio, 'Position', [5, 5, mask_radio_pos(3), mask_radio_pos(4)]);
        set(handles.mask_group, 'Position', [35 + mode_radio_pos(3), 15 + button_pos(4), ...
            10 + mask_radio_pos(3), 15 + 2 * mask_radio_pos(4)]);
    end
    resize(handles)
end
    
function resize(handles)
    figure_pos = get(handles.figure, 'Position');
    button_pos = get(handles.reset_button, 'Position');
    mode_radio_pos = get(handles.clear_radio, 'Position');
    y = 60 + button_pos(4) + 2 * mode_radio_pos(4);
    set(handles.axis, 'Position', [30, y, figure_pos(3) - 50, figure_pos(4) - y - 30]);
    set(handles.done_button, 'Position', [figure_pos(3) - button_pos(3) - 10, 10, ...
    button_pos(3), button_pos(4)]);
end

function [data_cells, starts] = split_data(data, mask)
    indices = find(mask);
    if isempty(indices)
        data_cells = [];
        starts = [];
        return;
    end
    starts = indices(2:end);
    starts = [indices(1), starts(indices(2:end) - indices(1:(end-1)) > 1)];
    num_starts = length(starts);
    data_cells = cell(1, num_starts);
    for i = 1:(num_starts - 1)
        indices = starts(i) + find(mask(starts(i):(starts(i+1)-1))) - 1;
        if indices(end) ~= length(data)
            indices = [indices, indices(end) + 1]; %#ok only sometime grows and we don't know the size
        end
        data_cells{i} = data(indices);
    end
    indices = starts(end) + find(mask(starts(end):end)) - 1;
    if indices(end) ~= length(data)
        indices = [indices, indices(end) + 1];
    end
    data_cells{num_starts} = data(indices);
end

function plot_with_masks(titleStr, data, mask_a, mask_b)   
    % A mask
    [a_data, a_starts] = split_data(data, mask_a);
    
    if ~isempty(mask_b)
        % B mask not counting any A mask
        [b_data, b_starts] = split_data(data, mask_b & (~mask_a));
        % no mask
        [u_data, u_starts] = split_data(data, ~(mask_a | mask_b));
    else
        % empty B mask
        b_data = [];
        b_starts = [];
        % no mask
        [u_data, u_starts] = split_data(data, ~mask_a);
    end
    
    starts = [u_starts, a_starts, b_starts];
    fused_data = [u_data, a_data, b_data];
    colors = [repmat('k', 1, length(u_starts)), repmat('c', 1, length(a_starts)), ...
        repmat('m', 1, length(b_starts))];
    [starts, idx] = sort(starts);
    fused_data = fused_data(idx);
    colors = colors(idx);
    for i = 1:length(starts)
        n = length(fused_data{i});
        plot(starts(i) - 1 + (1:n), fused_data{i}, colors(i));
        hold on
    end
    hold off
    
    lims = axis;
    n = length(data);
    dx = n / 20;
    axis([-dx, n + dx, lims(3), lims(4)]);
    title(titleStr);
end

function on_button_down(handles)
    user_data = get(handles.figure, 'UserData');
    point = get(handles.axis,'CurrentPoint');
    user_data.x_pos = point(1);
    user_data.mouseDown = true;
    set(handles.figure, 'UserData', user_data);
end

function on_mouth_move(handles)
    user_data = get(handles.figure, 'UserData');
    if ~isempty(user_data.x_pos)
        x_lim = get(handles.axis, 'XLim');
        y_lim = get(handles.axis, 'YLim');
        point = get(handles.axis, 'CurrentPoint');
        new_pos = max(x_lim(1), min(x_lim(2), point(1)));
        if user_data.is_clear
            if user_data.current_mask == 1
                color = 'b';
            else
                color = 'r';
            end
        else
            if user_data.current_mask == 1
                color = 'c';
            else
                color = 'm';
            end
        end
        set(user_data.patch, 'XData', [user_data.x_pos, user_data.x_pos, new_pos, new_pos], ...
            'YData', [y_lim(1), y_lim(2), y_lim(2), y_lim(1)], 'FaceColor', color);
    end
end

function on_button_up(handles)
    user_data = get(handles.figure, 'UserData');
    if ~isempty(user_data.x_pos)
        point = get(handles.axis, 'CurrentPoint');
        x_lim = get(handles.axis, 'XLim');
        new_pos = max(x_lim(1), min(x_lim(2), point(1)));
        n = length(user_data.default_mask_a);
        new_mask = false(1, n);
        indices = 1:n;
        new_mask(indices >= user_data.x_pos & indices <= new_pos) = true;
        if user_data.is_clear
            if user_data.current_mask == 1
                user_data.mask_a = user_data.mask_a & (~new_mask);
            else
                user_data.mask_b = user_data.mask_b & (~new_mask);
            end
        else
            if user_data.current_mask == 1
                user_data.mask_a = user_data.mask_a | new_mask;
            else
                user_data.mask_b = user_data.mask_b | new_mask;
            end
        end
        
        plot_with_masks(user_data.title, user_data.data, user_data.mask_a, user_data.mask_b);
        
        user_data.x_pos = [];
    end
    user_data.patch = patch([0, 0, 0, 0], [0, 0, 0, 0], 'c', 'FaceAlpha', .3, 'EdgeAlpha', 0);
    set(handles.figure, 'UserData', user_data);
end

function on_mode_change(handles, e)
    user_data = get(handles.figure, 'UserData');
    user_data.is_clear = strcmp(get(e.NewValue, 'String'), 'Clear');
    set(handles.figure, 'UserData', user_data);
end

function on_mask_change(handles, e)
    user_data = get(handles.figure, 'UserData');
    if strcmp(get(e.NewValue, 'String'), 'Mask A')
        user_data.current_mask = 1;
    else
        user_data.current_mask = 2;
    end
    set(handles.figure, 'UserData', user_data);
end

function on_reset(handles)
    user_data = get(handles.figure, 'UserData');
    user_data.mask_a = user_data.default_mask_a;
    user_data.mask_b = user_data.default_mask_b;
    plot_with_masks(user_data.title, user_data.data, user_data.mask_a, user_data.mask_b);
    user_data.patch = patch([0, 0, 0, 0], [0, 0, 0, 0], 'c', 'FaceAlpha', .3, 'EdgeAlpha', 0);
    set(handles.figure, 'UserData', user_data);
end

function on_auto_mask(handles)
    user_data = get(handles.figure, 'UserData');
    user_data.mask_a = user_data.auto_mask;
    plot_with_masks(user_data.title, user_data.data, user_data.mask_a, user_data.mask_b);
    user_data.patch = patch([0, 0, 0, 0], [0, 0, 0, 0], 'c', 'FaceAlpha', .3, 'EdgeAlpha', 0);
    set(handles.figure, 'UserData', user_data);
end
        