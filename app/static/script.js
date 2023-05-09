var getUrlParameter = function getUrlParameter(sParam) {
  var sPageURL = window.location.search.substring(1),
      sURLVariables = sPageURL.split('&'),
      sParameterName,
      i;
  for (i = 0; i < sURLVariables.length; i++) {
      sParameterName = sURLVariables[i].split('=');
      if (sParameterName[0] === sParam) {
          return sParameterName[1] === undefined ? true : decodeURIComponent(sParameterName[1]);
      }
  }
  return false;
}

$(document).ready(function() {
    // запрос на регистрацию
    $('#signupForm').on('submit', function(e) {
        e.preventDefault()

        $.ajax({
          processData: false,
          contentType: false,
          data : new FormData(this),
          type : 'post',
          url : '/signup',
          success: response => {
            // document.write(response)
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

    // запрос на авторизацию
    $('#loginForm').on('submit', function(e) {
      e.preventDefault()

      $.ajax({
        data : $(this).serialize(),
        type : 'post',
        url : '/login',
        success: response => {
          // document.write(response)
          window.location.reload()
        },
        error: response => {
          // TODO: в метод
          $(this).find('.error-block').text('')

          errors = response.responseJSON
          for (let key in errors) {
            $(this).find(`[data-field="${key}"]`).text(errors[key].join('\n'))
          }
        }
      })
    })

    // заполнение информации об автомобиле на формах
    $('#newAdForm, #filtersForm').each(function() {
      const selects = $(this).find('.car-info-select')

      for (let i = 0; i < selects.length - 1; i++) {
        selects.eq(i).on('change', function(e) {
          const value = $(this).val()
          const nextSelect = selects.eq(i+1)

          $.ajax({
            type: 'get',
            url: encodeURIComponent(`${$(this).data('fill-next-method')}/${value}`),
            beforeSend: () => {
              nextSelect.children().slice(1).remove()
            },
            success: response => {
              nextSelect.prop('disabled', false)

              for (let key in response) {
                nextSelect.append(`<option value=${key}>${response[key]}</option>`)
              }

              if ($(this).closest('form').attr('id') === 'filtersForm') {
                // после перезагрузки настройки фильтрации сохраняются
                resetSelect(
                  formId='filtersForm',
                  urlParamName=nextSelect.attr('name'),
                  needToTrigger=true
                )
              }
            },
            error: () => {
              nextSelect.prop('disabled', true)
            }
          })

          for (let j = i + 1; j < selects.length; j++) {
            selects.eq(j).children().slice(1).remove()
            selects.eq(j).prop('disabled', true)

            if (selects.eq(j).hasClass('generation-select')) {
              selects.eq(j).trigger('change')
            }
          }
        })
      }
    })

    // установка ограничений на год выпуска
    $('.generation-select').on('change', function(e) {
      const generationId = $(this).val()

      const yearInputsIds = {
        // новое объявление, год выпуска
        yearCreateAd: $(this).data('year'),

        // фильтрация поиска, год выпуска (нижняя граница)
        yearBeginFilters: $(this).data('year-begin'),

        // фильтрация поиска, год выпуска (верхняя граница)
        yearEndFilters: $(this).data('year-end'),
      }

      // запрашиваем годы выпуска, соответствующие поколению авто
      $.ajax({
        type: 'get',
        url: encodeURIComponent(`/release_years/${generationId}`),
        success: response => {
          const yearBegin = response.yearBegin.value
          const yearEnd = response.yearEnd.value
    
          // устанавливаем верхнюю и нижнюю границу года выпуска на инпуты
          for (let key of Object.keys(yearInputsIds)) {
            $(yearInputsIds[key]).attr({
              min: yearBegin,
              max: yearEnd
            })
          }
    
          if (!response.yearBegin.isDefault) {
            const currentValue = $(yearInputsIds.yearCreateAd).val()
    
            if (currentValue < yearBegin || currentValue > yearEnd) {
              $(yearInputsIds.yearCreateAd).val(yearBegin)
            }
      
            $(yearInputsIds.yearBeginFilters).val(yearBegin)
          }

          if (!response.yearBegin.isDefault) {
            $(yearInputsIds.yearEndFilters).val(yearEnd)
          }
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

          $('.color-picker').append(
            `<option value=${id} data-color="rgb(${red}, ${green}, ${blue})">${name}</option>`
          )

          resetSelect(formId='filtersForm', urlParamName='color')
        }
      }
    })

    $('.color-picker').on('change', function(e) {
      const currentColor = $(this).find(':selected').data('color')
      const colorSquare = $($(this).data('square'))

      if (currentColor) {
        colorSquare.removeClass('color-other')
        colorSquare.css('backgroundColor', currentColor)
      }
      else {
        colorSquare.addClass('color-other')
      }
    })

    // подгрузка населённых пунктов
    $.ajax({
      type: 'get',
      url: '/locations',
      success: response => {
        $('.location-datalist').each(function() {
          for (const id in response) {
            const name = response[id]
            $(this).append(`<option value="${name}">`)
          }
        })
      }
    })

    // запрос на добавление объявления
    $('#newAdForm').on('submit', function(e) {
      e.preventDefault()
      
      $.ajax({
        processData: false,
        contentType: false,
        data : new FormData(this),
        type : 'post',
        url : '/ad',
        success: response => {
          $('#newAdModal').modal('hide')
          $('#createAdSuccessModal').modal('show')
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

    // форматирование чисел в input type="number" (отделение разрядов пробелами)    
    $('.format-number').each(function() {
      $(this).text(
        $(this).text().replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
      )
    })

    // применение фильтров поиска
    $('#filtersForm').on('submit', function(e) {
      e.preventDefault()

      $.ajax({
        type: 'post',
        url: '/filter',
        data: $(this).serialize(),
        success: response => {
          $(this).find('.error-block').text('')

          // не отправляем csrf токен в get запросе
          $(this).find('[name="csrf_token"]').attr('name', '')

          window.location = '/?' + $(this).serialize()
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

    // отображение выбранных до перезагрузки страницы фильтров
    resetSelect(formId='filtersForm', urlParamName='transport_type', needToTrigger=true)
    resetSelect(formId='filtersForm', urlParamName='is_broken')
    resetSelect(formId='filtersForm', urlParamName='per_page')

    function resetSelect(formId, urlParamName, needToTrigger=false) {
      const urlParamValue = getUrlParameter(urlParamName)
      if (urlParamValue !== false) {
        const select = $(`#${formId} [name="${urlParamName}"]`)

        const index = select.find(`option[value="${urlParamValue}"]`).index()
        select.prop('selectedIndex', index)

        if (needToTrigger) {
          select.trigger('change')
        }
      }
    }

    // сброс фильтров
    $('#resetFilters').on('click', function(e) {
      window.location = '/?location='
    })
})