$(document).ready(function() {
    $('#signupForm').on('submit', function(e) {
        e.preventDefault()

        $.ajax({
          processData: false,
          contentType: false,
          data : new FormData(this),
          type : 'post',
          url : '/signup',
          success: response => {
            document.write(response)
            window.location.reload()
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
        type : 'post',
        url : '/login',
        success: response => {
          document.write(response)
          window.location.reload()
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

    carSettings = [
      { select: $('#transport_type'), queryNext: '/marks' },
      { select: $('#mark'), queryNext: '/models' },
      { select: $('#model'), queryNext: '/generations' },
      { select: $('#generation'), queryNext: '/series' },
      { select: $('#serie'), queryNext: '/modifications' },
      { select: $('#modification') }
    ]

    for (let i = 0; i < carSettings.length - 1; i++) {
      carSettings[i].select.on('change', function(e) {
        const value = carSettings[i].select.val()
        const nextSelect = carSettings[i+1].select

        $.ajax({
          type: 'get',
          url: encodeURIComponent(`${carSettings[i].queryNext}/${value}`),
          beforeSend: () => {
            nextSelect.children().slice(1).remove()
          },
          success: response => {
            nextSelect.prop('disabled', false)

            for (let key in response) {
              nextSelect.append(`<option value=${key}>${response[key]}</option>`)
            }
          },
          error: () => {
            nextSelect.prop('disabled', true)
          }
        })

        for (let j = i + 1; j < carSettings.length; j++) {
          carSettings[j].select.children().slice(1).remove()
          carSettings[j].select.prop('disabled', true)
        }
      })
    }

    $('#generation').on('change', function(e) {
      const value = $(this).val()

      $.ajax({
        type: 'get',
        url: encodeURIComponent(`/release_years/${value}`),
        success: response => {
          const releaseYearInputValue = $('#release_year').val()
          const yearBegin = response.yearBegin
          const yearEnd = response.yearEnd

          $('#release_year').attr('min', yearBegin)
          if (releaseYearInputValue < yearBegin) {
            $('#release_year').val(yearBegin)
          }

          $('#release_year').attr('max', yearEnd)
          if (releaseYearInputValue > yearEnd) {
            $('#release_year').val(yearEnd)
          }
        },
        error: () => {
          $('#release_year').attr('min', 1900)
          $('#release_year').attr('max', 2100)
        }
      })
    })

    // заполнение цветов
    $.ajax({
      type: 'get',
      url: '/colors',
      success: response => {
        for (const id in response) {
          const name = response[id].name,
                red = response[id].red,
                green = response[id].green,
                blue = response[id].blue

          $('#color').append(`<option value=${id} data-color="rgb(${red}, ${green}, ${blue})">${name}</option>`)
        }
      }
    })

    $('#color').on('change', function(e) {
      const currentColor = $(this).find(':selected').data('color')
      if (currentColor) {
        $('#color-square').removeClass('color-other')
        $('#color-square').css('backgroundColor', currentColor)
      }
      else {
        $('#color-square').addClass('color-other')
      }
    })

    // подгрузка населённых пунктов
    $.ajax({
      type: 'get',
      url: '/locations',
      success: response => {
        for (const id in response) {
          const name = response[id]
          $('#location-datalist').append(`<option value="${name}"">`)
        }
      }
    })

    $('#newAdForm').on('submit', function(e) {
      e.preventDefault()
      
      $.ajax({
        processData: false,
        contentType: false,
        data : new FormData(this),
        type : 'post',
        url : '/ad',
        success: response => {
          console.log('success')
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
})