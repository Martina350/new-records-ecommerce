function inicializarAplicacion() {
  inicializarSidebar();
  inicializarToasts();
  inicializarNavLanding();
  inicializarModalesAuth();
  inicializarValidacionesAuth();

  const formulario = document.getElementById('contactForm');
  if (formulario) {
    formulario.addEventListener('submit', (e) => {
      e.preventDefault();

      if (validarFormulario()) {
        mostrarExito(formulario);
      } else {
        alert('Por favor, corrige los errores en el formulario.');
      }
    }, { capture: true });
  }

  configurarFormularioTarjeta();
}

function sincronizarClaseBody(evento) {
  const detalle = evento.detail;
  if (
    !detalle ||
    !detalle.shouldSwap ||
    detalle.target !== document.body ||
    !detalle.xhr ||
    !detalle.xhr.responseText.includes('<body')
  ) return;

  const documentoNuevo = new DOMParser().parseFromString(
    detalle.xhr.responseText,
    'text/html'
  );
  if (documentoNuevo.body) {
    document.body.className = documentoNuevo.body.className;
  }
}

function mostrarTransicionClasica() {
  if (document.body) document.body.classList.add('navegacion-clasica');
}

function inicializarRespaldoNavegacion() {
  if (document.documentElement.dataset.respaldoNavegacion === 'activo') return;
  document.documentElement.dataset.respaldoNavegacion = 'activo';

  document.addEventListener('click', (evento) => {
    if (window.htmx || evento.defaultPrevented || evento.button !== 0) return;
    if (evento.metaKey || evento.ctrlKey || evento.shiftKey || evento.altKey) return;

    const enlace = evento.target.closest('a[href]');
    if (!enlace || enlace.hasAttribute('download')) return;
    if (enlace.target && enlace.target !== '_self') return;

    const destino = new URL(enlace.href, window.location.href);
    const esAnclaLocal =
      destino.pathname === window.location.pathname &&
      destino.search === window.location.search &&
      destino.hash;

    if (destino.origin === window.location.origin && !esAnclaLocal) {
      mostrarTransicionClasica();
    }
  });

  document.addEventListener('submit', (evento) => {
    if (window.htmx || evento.defaultPrevented) return;
    const formulario = evento.target;
    if (!(formulario instanceof HTMLFormElement)) return;
    if (formulario.target && formulario.target !== '_self') return;
    mostrarTransicionClasica();
  });

  window.addEventListener('pageshow', () => {
    if (document.body) document.body.classList.remove('navegacion-clasica');
  });
}

document.addEventListener('DOMContentLoaded', () => {
  inicializarAplicacion();
  inicializarRespaldoNavegacion();
});

document.addEventListener('htmx:beforeSwap', sincronizarClaseBody);
document.addEventListener('htmx:afterSettle', inicializarAplicacion);

/**
 * Control del Menú Móvil en la Cabecera de Inicio (Landing)
 */
function inicializarNavLanding() {
  const btnToggle = document.getElementById('btnToggleNavLanding');
  const navMovil = document.getElementById('navMovilLanding');
  if (!btnToggle || !navMovil) return;

  btnToggle.addEventListener('click', () => {
    const abierto = navMovil.classList.toggle('abierto');
    btnToggle.setAttribute('aria-expanded', String(abierto));
  });

  navMovil.querySelectorAll('a').forEach((enlace) => {
    enlace.addEventListener('click', () => {
      navMovil.classList.remove('abierto');
      btnToggle.setAttribute('aria-expanded', 'false');
    });
  });
}

/**
 * Control del Sidebar Lateral: Colapsar/Expandir en Desktop,
 * Slide-over en Móvil, Acordeones Jerárquicos y Auto-expansión.
 */
function inicializarSidebar() {
  const sidebar = document.getElementById('sidebar');
  const layoutApp = document.getElementById('layoutApp');
  const btnColapso = document.getElementById('btnColapsoSidebar');
  const btnMobileToggle = document.getElementById('btnToggleSidebarMobile');
  const btnMobileClose = document.getElementById('btnCerrarSidebarMobile');
  const backdrop = document.getElementById('sidebarBackdrop');

  if (!sidebar) return;

  // Restaurar estado de colapso en Desktop desde localStorage
  const sidebarGuardadoColapsado = localStorage.getItem('sidebar_colapsado') === 'true';
  if (sidebarGuardadoColapsado && window.innerWidth >= 1024) {
    sidebar.classList.add('is-collapsed');
    if (layoutApp) layoutApp.classList.add('sidebar-colapsada');
  }

  // Alternar Colapso en Desktop
  if (btnColapso) {
    btnColapso.addEventListener('click', () => {
      const estaColapsado = sidebar.classList.toggle('is-collapsed');
      if (layoutApp) layoutApp.classList.toggle('sidebar-colapsada', estaColapsado);
      localStorage.setItem('sidebar_colapsado', String(estaColapsado));
    });
  }

  // Apertura y Cierre en Dispositivos Móviles
  const toggleMobileSidebar = (abrir) => {
    sidebar.classList.toggle('abierto-movil', abrir);
    if (backdrop) backdrop.classList.toggle('visible', abrir);
    if (btnMobileToggle) btnMobileToggle.setAttribute('aria-expanded', String(abrir));
    document.body.style.overflow = abrir ? 'hidden' : '';
  };

  if (btnMobileToggle) {
    btnMobileToggle.addEventListener('click', () => {
      toggleMobileSidebar(!sidebar.classList.contains('abierto-movil'));
    });
  }

  if (btnMobileClose) {
    btnMobileClose.addEventListener('click', () => toggleMobileSidebar(false));
  }

  if (backdrop) {
    backdrop.addEventListener('click', () => toggleMobileSidebar(false));
  }

  // Cerrar sidebar móvil con tecla Escape sin duplicar el evento tras cada navegación.
  document.removeEventListener('keydown', manejarEscapeSidebar);
  document.addEventListener('keydown', manejarEscapeSidebar);

  // Cerrar al pulsar un enlace de navegación en móvil
  sidebar.querySelectorAll('a').forEach((enlace) => {
    enlace.addEventListener('click', () => {
      if (window.innerWidth < 1024) {
        toggleMobileSidebar(false);
      }
    });
  });

  // Acordeones Jerárquicos (Submódulos)
  const acordeonBotones = sidebar.querySelectorAll('.btn-acordeon-sidebar');
  acordeonBotones.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const submodulo = btn.closest('.submodulo-sidebar');
      if (!submodulo) return;

      const estaAbierto = submodulo.classList.toggle('abierto');
      btn.setAttribute('aria-expanded', String(estaAbierto));
    });
  });

  // Auto-expansión del submenú activo basado en la ruta actual
  const subitems = sidebar.querySelectorAll('.submodulo-sidebar');
  const rutaActual = window.location.pathname;

  subitems.forEach((submodulo) => {
    const enlaceActivo = submodulo.querySelector('.enlace-subitem.activo') ||
      Array.from(submodulo.querySelectorAll('.enlace-subitem')).some((a) => {
        const href = a.getAttribute('href');
        return href && rutaActual.startsWith(href);
      });

    if (enlaceActivo) {
      submodulo.classList.add('abierto');
      const btn = submodulo.querySelector('.btn-acordeon-sidebar');
      if (btn) btn.setAttribute('aria-expanded', 'true');
    }
  });
}

function manejarEscapeSidebar(evento) {
  const sidebar = document.getElementById('sidebar');
  if (evento.key !== 'Escape' || !sidebar?.classList.contains('abierto-movil')) return;

  sidebar.classList.remove('abierto-movil');
  document.getElementById('sidebarBackdrop')?.classList.remove('visible');
  document.getElementById('btnToggleSidebarMobile')?.setAttribute('aria-expanded', 'false');
  document.body.style.overflow = '';
}

/**
 * Sistema de Notificaciones Toast Flotantes con Auto-cierre
 */
function inicializarToasts() {
  const toasts = document.querySelectorAll('.toast-alerta');
  
  toasts.forEach((toast) => {
    const cerrar = () => {
      toast.classList.add('toast-salida');
      toast.addEventListener('animationend', () => {
        toast.remove();
      }, { once: true });
    };

    const btnCerrar = toast.querySelector('.btn-cerrar-toast');
    if (btnCerrar) {
      btnCerrar.addEventListener('click', cerrar);
    }

    // Auto-cierre después de 4.5 segundos
    setTimeout(() => {
      if (toast.isConnected && !toast.classList.contains('toast-salida')) {
        cerrar();
      }
    }, 4500);
  });
}

function configurarFormularioTarjeta() {
  const formularioTarjeta = document.getElementById('form-tarjeta');
  if (!formularioTarjeta) return;

  const numero = document.getElementById('numero');
  const mes = document.getElementById('mes_vencimiento');
  const anio = document.getElementById('anio_vencimiento');

  numero.addEventListener('input', () => {
    const digitos = numero.value.replace(/\D/g, '').slice(0, 19);
    numero.value = digitos.replace(/(.{4})/g, '$1 ').trim();
    numero.setCustomValidity('');
  });

  formularioTarjeta.addEventListener('submit', (evento) => {
    const digitos = numero.value.replace(/\D/g, '');
    numero.setCustomValidity(
      validarNumeroLuhn(digitos) ? '' : 'Ingresa un número de tarjeta válido.'
    );

    const anioActual = Number(formularioTarjeta.dataset.anioActual);
    const mesActual = Number(formularioTarjeta.dataset.mesActual);
    const mesIngresado = Number(mes.value);
    const anioIngresado = Number(anio.value);
    const vencimientoValido =
      mesIngresado >= 1 &&
      mesIngresado <= 12 &&
      (anioIngresado > anioActual ||
        (anioIngresado === anioActual && mesIngresado >= mesActual)) &&
      anioIngresado <= anioActual + 20;

    anio.setCustomValidity(
      vencimientoValido ? '' : 'La tarjeta está vencida o su fecha no es válida.'
    );

    if (!formularioTarjeta.checkValidity()) {
      evento.preventDefault();
      formularioTarjeta.reportValidity();
    }
  }, { capture: true });
}

function validarNumeroLuhn(numero) {
  if (!/^\d{13,19}$/.test(numero)) return false;

  let total = 0;
  [...numero].reverse().forEach((caracter, indice) => {
    let digito = Number(caracter);
    if (indice % 2 === 1) {
      digito *= 2;
      if (digito > 9) digito -= 9;
    }
    total += digito;
  });
  return total % 10 === 0;
}

function validarFormulario() {
  let esValido = true;

  const nombre = document.getElementById('name');
  const valorNombre = nombre.value.trim();

  if (valorNombre === '' || valorNombre.length < 3) {
    nombre.classList.add('no-valido');
    mostrarError('nameError', valorNombre === '' ? 'El nombre es obligatorio.' : 'El nombre debe tener al menos 3 caracteres.');
    esValido = false;
  } else {
    nombre.classList.remove('no-valido');
    ocultarError('nameError');
  }

  const ciudad = document.getElementById('city');
  const valorCiudad = ciudad.value.trim();

  if (valorCiudad === '') {
    ciudad.classList.add('no-valido');
    mostrarError('cityError', 'La ciudad es obligatoria.');
    esValido = false;
  } else {
    ciudad.classList.remove('no-valido');
    ocultarError('cityError');
  }

  const email = document.getElementById('email');
  const valorEmail = email.value.trim();
  const regexEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  if (valorEmail === '') {
    email.classList.add('no-valido');
    mostrarError('emailError', 'El email es obligatorio.');
    esValido = false;
  } else if (!regexEmail.test(valorEmail)) {
    email.classList.add('no-valido');
    mostrarError('emailError', 'Introduce un email válido.');
    esValido = false;
  } else {
    email.classList.remove('no-valido');
    ocultarError('emailError');
  }

  const asunto = document.getElementById('subject');
  const valorAsunto = asunto.value.trim();

  if (valorAsunto === '') {
    asunto.classList.add('no-valido');
    mostrarError('subjectError', 'El asunto es obligatorio.');
    esValido = false;
  } else {
    asunto.classList.remove('no-valido');
    ocultarError('subjectError');
  }

  const descripcion = document.getElementById('description');
  const valorDescripcion = descripcion.value.trim();

  if (valorDescripcion === '' || valorDescripcion.length < 10) {
    descripcion.classList.add('no-valido');
    mostrarError('descriptionError', valorDescripcion === '' ? 'El mensaje es obligatorio.' : 'La descripción debe tener al menos 10 caracteres.');
    esValido = false;
  } else {
    descripcion.classList.remove('no-valido');
    ocultarError('descriptionError');
  }

  return esValido;
}

function mostrarError(idElemento, mensaje) {
  const elemento = document.getElementById(idElemento);
  if (elemento) {
    elemento.textContent = mensaje;
    elemento.classList.add('visible');
  }
}

function ocultarError(idElemento) {
  const elemento = document.getElementById(idElemento);
  if (elemento) {
    elemento.textContent = '';
    elemento.classList.remove('visible');
  }
}

function mostrarExito(formulario) {
  const mensajeExito = document.getElementById('successMessage');
  if (mensajeExito) mensajeExito.classList.add('visible');
  formulario.reset();
  formulario.querySelectorAll('input, textarea').forEach((input) => input.classList.remove('no-valido'));
  ocultarError('nameError');
  ocultarError('cityError');
  ocultarError('emailError');
  ocultarError('subjectError');
  ocultarError('descriptionError');
}

/**
 * Control de Modales de Autenticación con Desenfoque de Pantalla de Inicio
 */
function inicializarModalesAuth() {
  const modalLogin = document.getElementById('modalLoginOverlay');
  const modalRegistro = document.getElementById('modalRegistroOverlay');
  const seccionInicio = document.getElementById('seccionInicio');

  const abrirModal = (modal) => {
    if (!modal) return;
    if (modalLogin) modalLogin.classList.remove('activo');
    if (modalRegistro) modalRegistro.classList.remove('activo');
    modal.classList.add('activo');
    if (seccionInicio) seccionInicio.classList.add('desenfocado');
  };

  const cerrarModales = () => {
    if (modalLogin) modalLogin.classList.remove('activo');
    if (modalRegistro) modalRegistro.classList.remove('activo');
    if (seccionInicio) seccionInicio.classList.remove('desenfocado');
  };

  const btnsHeaderLogin = document.querySelectorAll('.btn-abrir-login, .enlace-login-header, #btnHeaderLogin');
  btnsHeaderLogin.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      if (modalLogin && seccionInicio) {
        e.preventDefault();
        abrirModal(modalLogin);
      }
    });
  });

  const btnsHeroRegistro = document.querySelectorAll('.btn-abrir-registro, #btnHeroRegistro');
  btnsHeroRegistro.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      if (modalRegistro && seccionInicio) {
        e.preventDefault();
        abrirModal(modalRegistro);
      }
    });
  });

  // Botones de cierre X
  const btnCerrarLogin = document.getElementById('btnCerrarLoginModal');
  const btnCerrarRegistro = document.getElementById('btnCerrarRegistroModal');
  if (btnCerrarLogin) btnCerrarLogin.addEventListener('click', cerrarModales);
  if (btnCerrarRegistro) btnCerrarRegistro.addEventListener('click', cerrarModales);

  // Cerrar al dar clic en el backdrop exterior
  [modalLogin, modalRegistro].forEach((modal) => {
    if (!modal) return;
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        cerrarModales();
      }
    });
  });

  // Alternar entre Login y Registro dentro del Modal
  document.querySelectorAll('.btn-cambiar-a-registro').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      abrirModal(modalRegistro);
    });
  });

  document.querySelectorAll('.btn-cambiar-a-login').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      abrirModal(modalLogin);
    });
  });

  // Cerrar con Escape sin acumular listeners tras cada navegación parcial.
  document.removeEventListener('keydown', manejarEscapeModales);
  document.addEventListener('keydown', manejarEscapeModales);
}

function manejarEscapeModales(evento) {
  if (evento.key !== 'Escape') return;

  document.getElementById('modalLoginOverlay')?.classList.remove('activo');
  document.getElementById('modalRegistroOverlay')?.classList.remove('activo');
  document.getElementById('seccionInicio')?.classList.remove('desenfocado');
}

/**
 * Validaciones dinámicas e interactivas debajo de cada campo
 * para los formularios de Registro y Login (sin popups ni toasts).
 */
function inicializarValidacionesAuth() {
  const formulariosRegistro = document.querySelectorAll('#formRegistro, #formRegistroLanding');
  formulariosRegistro.forEach((form) => {
    const inputNombre = form.querySelector('input[name="nombre"]');
    const inputEmail = form.querySelector('input[name="email"]');
    const inputPassword = form.querySelector('input[name="password"]');
    const inputConfirmar = form.querySelector('input[name="confirmar_password"]');

    const getErrorSpan = (input) => {
      if (!input) return null;
      const grupo = input.closest('.grupo-formulario');
      return grupo ? grupo.querySelector('.mensaje-error') : null;
    };

    const spanNombreError = getErrorSpan(inputNombre);
    const spanEmailError = getErrorSpan(inputEmail);
    const spanPasswordError = getErrorSpan(inputPassword);
    const spanConfirmarError = getErrorSpan(inputConfirmar);

    const setFieldError = (input, span, mensaje) => {
      if (input) input.classList.add('no-valido');
      if (span) {
        span.textContent = mensaje;
        span.classList.add('visible');
      }
    };

    const clearFieldError = (input, span) => {
      if (input) input.classList.remove('no-valido');
      if (span) {
        span.textContent = '';
        span.classList.remove('visible');
      }
    };

    const validarNombre = () => {
      if (!inputNombre) return true;
      const valor = inputNombre.value.trim();
      if (!valor) {
        setFieldError(inputNombre, spanNombreError, 'El nombre completo es un campo obligatorio.');
        return false;
      }
      if (valor.length < 2 || valor.length > 100) {
        setFieldError(inputNombre, spanNombreError, 'El nombre debe contener entre 2 y 100 caracteres.');
        return false;
      }
      clearFieldError(inputNombre, spanNombreError);
      return true;
    };

    const validarEmail = () => {
      if (!inputEmail) return true;
      const valor = inputEmail.value.trim();
      const regexEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!valor) {
        setFieldError(inputEmail, spanEmailError, 'El correo es un campo obligatorio.');
        return false;
      }
      if (!regexEmail.test(valor)) {
        setFieldError(inputEmail, spanEmailError, 'El correo debe ser un correo válido.');
        return false;
      }
      clearFieldError(inputEmail, spanEmailError);
      return true;
    };

    const validarPassword = () => {
      if (!inputPassword) return true;
      const valor = inputPassword.value;
      if (!valor) {
        setFieldError(inputPassword, spanPasswordError, 'La contraseña es un campo obligatorio.');
        return false;
      }
      if (valor.length < 8) {
        setFieldError(inputPassword, spanPasswordError, 'La contraseña debe tener mínimo 8 caracteres.');
        return false;
      }
      clearFieldError(inputPassword, spanPasswordError);
      return true;
    };

    const validarConfirmacion = () => {
      if (!inputConfirmar || !inputPassword) return true;
      const pass = inputPassword.value;
      const confirm = inputConfirmar.value;
      if (!confirm) {
        setFieldError(inputConfirmar, spanConfirmarError, 'Confirmar contraseña es un campo obligatorio.');
        return false;
      }
      if (pass !== confirm) {
        setFieldError(inputConfirmar, spanConfirmarError, 'La contraseña debe coincidir.');
        return false;
      }
      clearFieldError(inputConfirmar, spanConfirmarError);
      return true;
    };

    if (inputNombre) {
      inputNombre.addEventListener('input', validarNombre);
      inputNombre.addEventListener('blur', validarNombre);
    }
    if (inputEmail) {
      inputEmail.addEventListener('input', validarEmail);
      inputEmail.addEventListener('blur', validarEmail);
    }
    if (inputPassword) {
      inputPassword.addEventListener('input', () => {
        validarPassword();
        if (inputConfirmar && inputConfirmar.value) validarConfirmacion();
      });
      inputPassword.addEventListener('blur', validarPassword);
    }
    if (inputConfirmar) {
      inputConfirmar.addEventListener('input', validarConfirmacion);
      inputConfirmar.addEventListener('blur', validarConfirmacion);
    }

    form.addEventListener('submit', (e) => {
      const v1 = validarNombre();
      const v2 = validarEmail();
      const v3 = validarPassword();
      const v4 = validarConfirmacion();
      if (!v1 || !v2 || !v3 || !v4) {
        e.preventDefault();
      }
    }, { capture: true });
  });

  const formulariosLogin = document.querySelectorAll('#formLogin, #formLoginLanding');
  formulariosLogin.forEach((form) => {
    const inputEmail = form.querySelector('input[name="email"]');
    const inputPassword = form.querySelector('input[name="password"]');

    const getErrorSpan = (input) => {
      if (!input) return null;
      const grupo = input.closest('.grupo-formulario');
      return grupo ? grupo.querySelector('.mensaje-error') : null;
    };

    const spanEmailError = getErrorSpan(inputEmail);
    const spanPasswordError = getErrorSpan(inputPassword);

    const setFieldError = (input, span, mensaje) => {
      if (input) input.classList.add('no-valido');
      if (span) {
        span.textContent = mensaje;
        span.classList.add('visible');
      }
    };

    const clearFieldError = (input, span) => {
      if (input) input.classList.remove('no-valido');
      if (span) {
        span.textContent = '';
        span.classList.remove('visible');
      }
    };

    const validarLoginEmail = () => {
      if (!inputEmail) return true;
      const valor = inputEmail.value.trim();
      const regexEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!valor) {
        setFieldError(inputEmail, spanEmailError, 'El correo electrónico es un campo obligatorio.');
        return false;
      }
      if (!regexEmail.test(valor)) {
        setFieldError(inputEmail, spanEmailError, 'El correo debe ser un correo válido.');
        return false;
      }
      clearFieldError(inputEmail, spanEmailError);
      return true;
    };

    const validarLoginPassword = () => {
      if (!inputPassword) return true;
      const valor = inputPassword.value;
      if (!valor) {
        setFieldError(inputPassword, spanPasswordError, 'La contraseña es un campo obligatorio.');
        return false;
      }
      clearFieldError(inputPassword, spanPasswordError);
      return true;
    };

    if (inputEmail) {
      inputEmail.addEventListener('input', validarLoginEmail);
      inputEmail.addEventListener('blur', validarLoginEmail);
    }
    if (inputPassword) {
      inputPassword.addEventListener('input', validarLoginPassword);
      inputPassword.addEventListener('blur', validarLoginPassword);
    }

    form.addEventListener('submit', (e) => {
      const v1 = validarLoginEmail();
      const v2 = validarLoginPassword();
      if (!v1 || !v2) {
        e.preventDefault();
      }
    }, { capture: true });
  });
}
