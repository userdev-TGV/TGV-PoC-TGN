const { useState, useMemo } = React;

const metricsConfig = [
  { key: 'saldo_cuotapartes', label: 'Saldo de cuotapartes' },
  { key: 'saldo_valorizado', label: 'Saldo valorizado (FIFO)' },
  { key: 'total_valuacion_impositiva', label: 'Valuación Impositiva' },
  { key: 'total_valuacion_contable', label: 'Valuación Contable' },
  { key: 'total_rentas_fuente_arg', label: 'Rentas fuente argentina (IIBB)' },
];

function Metric({ label, value }) {
  const formatted = useMemo(() => {
    if (value === null || value === undefined) return '—';
    return new Intl.NumberFormat('es-AR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  }, [value]);

  return React.createElement(
    'div',
    { className: 'metric' },
    React.createElement('p', { className: 'label' }, label),
    React.createElement('p', { className: 'value' }, formatted),
  );
}

function UploadActions({ sampleName, onSubmit, disabled }) {
  return React.createElement(
    'div',
    { className: 'action-row' },
    React.createElement(
      'button',
      { type: 'button', onClick: () => onSubmit(false), disabled },
      'Procesar archivo subido',
    ),
    React.createElement(
      'button',
      { type: 'button', className: 'secondary', onClick: () => onSubmit(true), disabled },
      `Usar ejemplo (${sampleName})`,
    ),
  );
}

function App({ sampleName }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [filename, setFilename] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    setSelectedFile(file || null);
    setFilename(file ? file.name : '');
    setError('');
  };

  const submit = async (useDefault) => {
    setError('');
    setLoading(true);

    try {
      const formData = new FormData();
      if (useDefault) {
        formData.append('use_default', '1');
      } else if (selectedFile) {
        formData.append('file', selectedFile);
      }

      const response = await fetch('/api/simulate', {
        method: 'POST',
        body: formData,
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || 'No se pudo procesar la simulación');
      }

      setResults({
        filename: payload.filename,
        metrics: payload.results,
      });
    } catch (err) {
      setResults(null);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return React.createElement(
    React.Fragment,
    null,
    React.createElement(
      'header',
      null,
      React.createElement('h1', null, 'Simulador de Automatización FCI (React)'),
      React.createElement(
        'p',
        null,
        'Subí un XLSX o usá el archivo de ejemplo y obtené los resultados del procesamiento.',
      ),
    ),
    React.createElement(
      'section',
      { className: 'card' },
      React.createElement('h2', null, 'Elegí el archivo a procesar'),
      React.createElement(
        'div',
        { className: 'upload-form' },
        React.createElement(
          'label',
          { className: 'file-input' },
          React.createElement('input', {
            type: 'file',
            accept: '.xlsx',
            onChange: handleFileChange,
          }),
          React.createElement('span', null, filename || 'Seleccionar XLSX'),
        ),
        React.createElement(UploadActions, {
          sampleName,
          onSubmit: submit,
          disabled: loading,
        }),
      ),
      React.createElement(
        'p',
        { className: 'muted' },
        'Si no elegís ningún archivo, podés correr la simulación con el XLSX de ejemplo.',
      ),
      error
        ? React.createElement(
            'div',
            { className: 'alert' },
            React.createElement('p', null, error),
          )
        : null,
    ),
    React.createElement(
      'section',
      { className: 'card' },
      React.createElement('h2', null, 'Estado'),
      React.createElement(
        'div',
        { className: 'status-row' },
        React.createElement(
          'span',
          { className: `tag ${loading ? 'tag--info' : 'tag--idle'}` },
          loading ? 'Procesando...' : 'Listo',
        ),
        results
          ? React.createElement('span', { className: 'muted' }, `Último archivo: ${results.filename}`)
          : React.createElement('span', { className: 'muted' }, 'Sin resultados todavía'),
      ),
    ),
    results
      ? React.createElement(
          'section',
          { className: 'card' },
          React.createElement('h2', null, 'Resultados de la simulación'),
          React.createElement('p', { className: 'muted' }, `Archivo: ${results.filename}`),
          React.createElement(
            'div',
            { className: 'grid' },
            metricsConfig.map((metric) =>
              React.createElement(Metric, {
                key: metric.key,
                label: metric.label,
                value: results.metrics?.[metric.key],
              }),
            ),
          ),
        )
      : null,
    React.createElement(
      'footer',
      null,
      React.createElement(
        'p',
        null,
        'La interfaz usa React y consulta al backend Flask para procesar el XLSX y consolidar los valores.',
      ),
    ),
  );
}

const rootEl = document.getElementById('root');
const sampleName = rootEl?.dataset?.sample || '';
const root = ReactDOM.createRoot(rootEl);
root.render(React.createElement(App, { sampleName }));
