var AdminForm = function() {
    this.applyStyle = function(el, name) {
        switch (name) {
            case 'chosen':
                $(el).chosen();
                break;
            case 'chosenblank':
                $(el).chosen({allow_single_deselect: true});
                break;
            case 'datepicker':
                $(el).datepicker();
                break;
            case 'datetimepicker':
                $(el).datepicker({displayTime: true});
                break;
        }
    };
};

$(document).on('click', '.append', function(e) {
    e.preventDefault();
    _this = $(this);
    parent = _this.parent();
    len = parent.find('>.field').length;
    html = parent.find('>.append-list').html();
    _new = $(html);
    _new.find('label,input,textarea,select').each(function(index) {
        __this = $(this);
        $.each(['id', 'name','for'], function(index, value) { 
            v = __this.attr(value);
            if (v) {
                new_v = v.replace("__new__", len);
                __this.attr(value,new_v);
            }
        });
    });
    _this.before(_new);
    auto_apply(_new);
    _new.hide().fadeOut(0);
    _new.slideDown(200);
    _new.dequeue();

    _new.fadeIn(200);
    return false;
});

$(document).on('click', '.field>.delete',function() {
    var p = $(this).parent();
    p.slideUp(200);
    p.dequeue();
    p.fadeOut(200,function(){ p.remove(); });  
});

$(document).on('click', 'legend > .delete',function() {
    $(this).parent().parent().remove();  
});

$('.search-input').keydown(function(ev) {
    if (ev.keyCode === 13) {
        ev.preventDefault();
        window.location.href = window.location.pathname + '?q=' + encodeURIComponent($(this).val());
    }
});

$('.search-input').on('input', function() {
    if ($(this).val().length) {
        $('.search .clear-btn').show();
    } else {
        $('.search .clear-btn').hide();
    }
});

$('.search .clear-btn').click(function() {
    $('.search .search-input').val('').focus();
    $(this).hide();
    window.location.href = window.location.pathname;
});

// Apply automatic styles
function auto_apply(el) {
    el.find('[data-role=chosen]:visible').chosen();
    el.find('[data-role=chosenblank]:visible').chosen({allow_single_deselect: true});
    el.find('[data-role=datepicker]:visible').datepicker();
    el.find('[data-role=datetimepicker]:visible').datepicker({displayTime: true});
}

auto_apply($(document));

