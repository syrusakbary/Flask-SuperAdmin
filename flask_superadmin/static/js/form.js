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
    };
  }
};

$('.append').live('click',function(e) {
    e.preventDefault();
    _this = $(this)
    parent = _this.parent()
    len = parent.find('>.field').length;
    html = parent.find('>.append-list').html();
    _new = $(html);
    _new.find('label,input,textarea,select').each(function(index) {
        __this = $(this);
        $.each(['id', 'name','for'], function(index, value) { 
            v = __this.attr(value)
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
$('.field>.delete').live('click',function() {
  var p = $(this).parent();
  p.slideUp(200);
  p.dequeue();
  p.fadeOut(200,function(){p.remove();});  
})
$('legend>.delete').live('click',function() {
  $(this).parent().parent().remove();  
})

// Apply automatic styles
function auto_apply(el) {
el.find('[data-role=chosen]:visible').chosen();
el.find('[data-role=chosenblank]:visible').chosen({allow_single_deselect: true});
el.find('[data-role=datepicker]:visible').datepicker();
el.find('[data-role=datetimepicker]:visible').datepicker({displayTime: true});
}
auto_apply($(document));