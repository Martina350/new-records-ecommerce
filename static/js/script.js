document.addEventListener('DOMContentLoaded', () => {
  const botonMenu = document.querySelector('.alternar-nav');
  const menuMobile = document.getElementById('navMovil');
  if (botonMenu && menuMobile) {
    botonMenu.addEventListener('click', () => {
      const estaAbierto = menuMobile.classList.toggle('abierto');
      botonMenu.setAttribute('aria-expanded', String(estaAbierto));
    });
  }

  const params = new URLSearchParams(window.location.search);
  const categoria = params.get('categoria');
  const tarjetas = document.querySelectorAll('.tarjeta-producto');
  if (tarjetas.length && categoria) {
    tarjetas.forEach((card) => {
      card.style.display = card.getAttribute('data-categoria') === categoria ? '' : 'none';
    });
  }

  const categoriaActiva = categoria || 'todos';
  document.querySelectorAll('.botones-filtro [data-categoria]').forEach((link) => {
    link.classList.toggle('activo', link.getAttribute('data-categoria') === categoriaActiva);
  });

  const formulario = document.getElementById('contactForm');

  if (formulario) {
    formulario.addEventListener('submit', (e) => {
      e.preventDefault();

      if (validarFormulario()) {
        mostrarExito(formulario);
      } else {
        alert('Por favor, corrige los errores en el formulario.');
      }
    });
  }

  configurarFormularioTarjeta();
});

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
  });
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

