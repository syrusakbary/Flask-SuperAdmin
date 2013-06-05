var AdminFilters = function(element, filters_element, adminForm, operations, options, types) {
    var $root = $(element);
    var $container = $('.filters', $root);
    var lastCount = 0;

    function getCount(name) {
        var idx = name.indexOf('_');
        return parseInt(name.substr(3, idx - 3), 10);
    }

    function changeOperation() {
        var $parent = $(this).parent();
        var $el = $('.filter-val', $parent);
        var count = getCount($el.attr('name'));
        $el.attr('name', 'flt' + count + '_' + $(this).val());
        $('button', $root).show();
    }

    function removeFilter() {
        $(this).parent().remove();
        $('button', $root).show();
    }

    function addFilter(name, op) {
        var $el = $('<div class="filter-row" />').appendTo($container);

        $('<a href="#" class="btn remove-filter" />')
                .append($('<span class="close-icon">&times;</span>'))
                .append('&nbsp;')
                .append(name)
                .appendTo($el)
                .click(removeFilter);

        var $select = $('<select class="filter-op" />')
                      .appendTo($el)
                      .change(changeOperation);

        $(op).each(function() {
            $select.append($('<option/>').attr('value', this[0]).text(this[1]));
        });

        $select.chosen();

        var optId = op[0][0];

        var $field;

        if (optId in options) {
            $field = $('<select class="filter-val" />')
                        .attr('name', 'flt' + lastCount + '_' + optId)
                        .appendTo($el);

            $(options[optId]).each(function() {
                $field.append($('<option/>')
                    .val(this[0]).text(this[1]))
                    .appendTo($el);
            });

            $field.chosen();
        } else
        {
            $field = $('<input type="text" class="filter-val" />')
                        .attr('name', 'flt' + lastCount + '_' + optId)
                        .appendTo($el);
        }

        if (optId in types) {
            $field.attr('data-role', types[optId]);
            adminForm.applyStyle($field, types[optId]);
        }

        lastCount += 1;
    }

    $('a.filter', filters_element).click(function() {
        var name = $(this).text().trim();

        addFilter(name, operations[name]);

        $('button', $root).show();
    });

    $('.filter-op', $root).change(changeOperation);
    $('.filter-val', $root).change(function() {
        $('button', $root).show();
    });
    $('.remove-filter', $root).click(removeFilter);

    $('.filter-val', $root).each(function() {
        var count = getCount($(this).attr('name'));
        if (count > lastCount)
            lastCount = count;
    });

    lastCount += 1;
};

    checker = $( ':checkbox[value="all"]' );
    checker.click(function(){
        all_checkboxes.attr( 'checked', $( this ).is( ':checked' ) ).change();
    });
    all_checkboxes = $( ':checkbox[name="_selected_action"]' ).not(checker);
    actions = $('.actions').change(function() {this.form.submit();});
    actions = actions.chosen().data('chosen').container.addClass(actions.attr('class'));
    all_checkboxes.change(function(e) {
        _this = $(this);
        checked = $.grep(all_checkboxes, function (a) { return $(a).is( ':checked' ); });
        all_selected = checked.length === all_checkboxes.length;
        opacity = (all_selected || checked.length === 0) ? 1 : 0.5;
        checker.attr('checked',checked.length > 0).css('opacity', opacity);
        actions.toggleClass('hidden', checked.length === 0);
        // $('.action_delete').stop().animate({'opacity':checked.length>0?1:0},200)
        if (_this.is(':checked')) _this.parent().parent().addClass('checked');
        else _this.parent().parent().removeClass('checked');
    }).click(function(e) {e.stopPropagation();});
