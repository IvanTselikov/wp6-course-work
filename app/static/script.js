$(document).ready(function() {
    $('#signupForm').on('submit', function(e) {
        e.preventDefault()

        $.ajax({
          processData: false,
          contentType: false,
          data : new FormData(this),
          type : 'POST',
          url : '/signup',
          success: response => {
            document.write(response)
          },
          error: response => {
            $(this).find('.error-block').text('')

            errors = response.responseJSON
            for (let key in errors) {
              $(this).find(`[data-field="${key}"]`).text(errors[key].join('\n'))
            }
          }
        })
    })

    $('#loginForm').on('submit', function(e) {
      e.preventDefault()

      $.ajax({
        data : $(this).serialize(),
        type : 'POST',
        url : '/login',
        success: response => {
          document.write(response)
        },
        error: response => {
          // console.log($(this))
          $(this).find('.error-block').text('')

          errors = response.responseJSON
          for (let key in errors) {
            $(this).find(`[data-field="${key}"]`).text(errors[key].join('\n'))
          }
        }
      })
    })
})