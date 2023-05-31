function getCookie(name) {
  let matches = document.cookie.match(
    new RegExp(
      "(?:^|; )" +
        name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, "\\$1") +
        "=([^;]*)"
    )
  );
  return matches ? decodeURIComponent(matches[1]) : undefined;
}

function showErrors(form, response) {
  form.find('.error-block').text('')

  const errors = response.responseJSON
  let isFocused = false
  for (let key in errors) {
    if (!isFocused) {
      isFocused = true
      const input = form.find('#' + key)
      if (input) {
        input.focus()
      }
    }
    form.find(`[data-field="${key}"]`).text(errors[key].join('\n'))
  }
}


$(document).ready(function() {
    // показать/скрыть пароль
    $('.show-password-button').on('click', function() {
      const input = $(this).siblings('input')
      if (input.attr('type') === 'password') {
        // показать пароль
        input.attr('type', 'text')
        $(this).find('i').removeClass('fa-eye').addClass('fa-eye-slash')
      } else {
        // скрыть пароль
        input.attr('type', 'password')
        $(this).find('i').removeClass('fa-eye-slash').addClass('fa-eye')
      }
    })

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
            window.location.reload()
          },
          error: response => {
            showErrors($(this), response)
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
          window.location.reload()
        },
        error: response => {
          showErrors($(this), response)
        }
      })
    })

    // запрос на выход из аккаунта
    $('#logout-form').on('submit', function(e) {
      e.preventDefault()

      $.ajax({
        url : '/logout',
        success: () => {
          window.location.reload()
        }
      })
    })

    // заполнение информации об автомобиле на формах
    $('#newAdForm, #filtersForm, #edit-ad-form').each(function() {
      const selects = $(this).find('.car-info-select')

      for (let i = 0; i < selects.length - 1; i++) {
        selects.eq(i).on('change', function(e) {
          const value = $(this).val()
          const nextSelect = selects.eq(i+1)

          $.ajax({
            type: 'get',
            url: `${$(this).data('fill-next-method')}/${value}`,
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
                  cookieName=nextSelect.attr('name'),
                  needToTrigger=true
                )
              } else if ($(this).closest('form').attr('id') === 'edit-ad-form') {
                resetEditAdSelect(nextSelect.attr('name'))
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
        url: `/release_years/${generationId}`,
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
        url : '/ads',
        success: response => {
          $('#newAdModal').modal('hide')
          $('#createAdSuccessModal').modal('show')
        },
        error: response => {
          showErrors($(this), response)
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
      if (e.originalEvent.submitter.name !== 'reset') {
        e.preventDefault()

        $.ajax({
          type: 'post',
          url: '/filters',
          data: $(this).serialize(),
          success: () => {
            $(this).find('.error-block').text('')
            window.location = '/'
          },
          error: response => {
            showErrors($(this), response)
          }
        })
      }
    })

    // отображение выбранных до перезагрузки страницы фильтров
    resetSelect(formId='filtersForm', cookieName='transport_type', needToTrigger=true)
    resetSelect(formId='filtersForm', cookieName='is_broken')
    resetSelect(formId='filtersForm', cookieName='per_page')

    function resetSelect(formId, cookieName, needToTrigger=false) {
      const cookieValue = getCookie(cookieName)
      if (cookieValue !== undefined) {
        const select = $(`#${formId} [name="${cookieName}"]`)

        const index = select.find(`option[value="${cookieValue}"]`).index()
        select.prop('selectedIndex', index)

        if (needToTrigger) {
          select.trigger('change')
        }
      }
    }

    // действия с объявлениями

    function createConfirmModal(
      title,
      annotation,
      action,
      submitText,
      showMessageInput=false,
      method='post',
      queryBody=undefined
    ) {
      modal = $('#confirm-modal')

      modal.find('.modal-title').text(title)
      modal.find('.confirm-annotation').text(annotation)
      modal.find('form').attr('action', action)
      modal.find('button[type="submit"]').text(submitText)

      if (showMessageInput) {
        modal.find('form').removeClass('d-none')
      } else {
        modal.find('form').addClass('d-none')
      }

      if (method.toLowerCase().trim() !== 'post') {
        modal.find('form').on('submit', function(e) {
          e.preventDefault()

          fetch(action, {
            method: method, body: queryBody
          }).then(res => {
            if (res.redirected) {
                document.location = res.url;
            }
          })
        })
      }
      return modal
    }


    // публикация объявления (администратор)
    $('.publish-ad-button').on('click', function() {
      ad_id = $(this).closest('.dropdown').data('ad-id')
      status_id = 1

      modal = createConfirmModal(
        title='Публикация объявления',
        annotation='Вы уверены, что хотите разрешить публикацию данного объявления?',
        action=`/ads/${ad_id}/status/${status_id}`,
        submitText='Опубликовать',
        showMessageInput=false
      )

      modal.modal('show')
    })

    $('.ad-to-revision-button').on('click', function() {
      ad_id = $(this).closest('.dropdown').data('ad-id')
      status_id = 4

      modal = createConfirmModal(
        title='Отправка объявления на доработку',
        annotation='Причина (сообщение для владельца объявления):',
        action=`/ads/${ad_id}/status/${status_id}`,
        submitText='Отправить на доработку',
        showMessageInput=true
      )

      modal.modal('show')
    })

    // блокировать объявление
    $('.block-ad-button').on('click', function() {
      ad_id = $(this).closest('.dropdown').data('ad-id')
      status_id = 5

      modal = createConfirmModal(
        title='Заблокировать объявление',
        annotation='Причина (сообщение для владельца объявления):',
        action=`/ads/${ad_id}/status/${status_id}`,
        submitText='Заблокировать',
        showMessageInput=true
      )

      modal.modal('show')
    })


    // заполнение формы редактирования объявления
    let selectValues

    if ($('#edit-ad-form').length) {
      resetEditAdForm()
    }

    function resetEditAdForm() {
      const ad_id = window.location.pathname.substring(
        window.location.pathname.lastIndexOf('/') + 1
      )
  
      $.ajax({
        type: 'get',
        contentType: 'application/json',
        url: `/ads/${ad_id}`,
        success: response => {
          selectValues = response
          resetEditAdSelect('transport_type')
          resetEditAdSelect('color')
          resetEditAdSelect('pts_type')
  
          // установка описания
          $('#edit-ad-form [name="description"]').text(response['description'])
        }
      })  
    }
    
    function resetEditAdSelect(selectName) {      
      const select = $(`#edit-ad-form [name="${selectName}"]`)

      if (select.length) {
        const index = select.find(`option[value="${selectValues[selectName]}"]`).index()
        select.prop('selectedIndex', index)
  
        select.trigger('change')
      }
    }

    // запрос на обновление объявления
    $('#edit-ad-form').on('submit', function(e) {
      e.preventDefault()
      
      $.ajax({
        processData: false,
        contentType: false,
        data : new FormData(this),
        type : 'put',
        url : '/ads',
        success: response => {
          $('#edit-ad-modal').modal('hide')
          $('#editAdSuccessModal').modal('show')
        },
        error: response => {
          showErrors($(this), response)
        }
      })
    })

    // удаление объявления
    $('.delete-ad-button').on('click', function() {
      ad_id = $('#edit-ad-form input[name="ad_id"]').val()

      modal = createConfirmModal(
        title='Удаление объявления',
        annotation='Вы уверены, что хотите безвозвратно удалить объявление?',
        action=`/ads/${ad_id}`,
        submitText='Удалить',
        showMessageInput=false,
        method='delete',
      )

      modal.modal('show')
    })

    // редактирование профиля
    $('#edit-profile-form').on('submit', function(e) {
      e.preventDefault()

      const userLogin = window.location.pathname.substring(
        window.location.pathname.lastIndexOf('/') + 1
      )

      $.ajax({
        processData: false,
        contentType: false,
        data : new FormData(this),
        type : 'put',
        url : `/user/${userLogin}`,
        success: () => {
          window.location.reload()
        },
        error: response => {
          showErrors($(this), response)
        }
      })
    })
})