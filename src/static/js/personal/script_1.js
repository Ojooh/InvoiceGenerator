jQuery(document).ready(function ($) {
  var start = $('.start-btn');

  start.on('click', function (e) {
    e.preventDefault();
    e.stopPropagation();

    var url = '/invoice';
    var data = {};

    $.ajax({
      url: url,
      data: data,
      type: 'GET',
      beforeSend: function () {
        Swal.fire({
          title: 'Auto close alert!',
          html: 'Please Hold on as Invoice is being generated',
          timer: 400000,
          timerProgressBar: true,
          showConfirmButton: false,
          allowOutsideClick: false,
        });
      },
      success: function (data) {
        console.log(data['success']);
        if (data.success) {
          Swal.fire(
            data.success,
            'Click OK to proceed to List',
            'success'
          ).then(function () {
            $('.box-area').addClass('deactivated');
            $('.list').removeClass('deactivated');

            var list_html = '';
            var p = data.paths;

            for (var t = 0; t < p.length; p++) {
              list_html +=
                `<li class="text-center"><a href="/static/files/invoice-` +
                (t + 1).toString() +
                `.pdf" target="_blank">Invoice - ` +
                (t + 1).toString() +
                `</a></li>`;
            }
            console.log(list_html);
            $('.invoice').append(list_html);
          });
        } else {
          swal.close();
          //   msg = "<span class='alert alert-success'>" + data.error + '</span>';
          //   error.html(msg);
        }
      },
    });
  });
});
