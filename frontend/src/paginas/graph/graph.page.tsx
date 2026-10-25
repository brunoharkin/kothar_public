import React from 'react';

export function GraphPage() {
  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>🕸️ Code Graph 3D</h1>
        <p style={styles.subtitle}>Visão estrutural baseada no Codebase Memory MCP</p>
      </div>
      <div style={styles.iframeWrapper}>
        <iframe 
          src="/cbm-ui" 
          style={styles.iframe}
          title="Codebase Memory UI"
        />
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: '24px',
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    boxSizing: 'border-box',
  },
  header: {
    marginBottom: '20px',
  },
  title: {
    fontSize: '1.75rem',
    fontWeight: 'bold',
    color: '#c9d1d9',
    margin: '0 0 8px 0',
  },
  subtitle: {
    color: '#8b949e',
    margin: 0,
    fontSize: '0.95rem',
  },
  iframeWrapper: {
    flex: 1,
    backgroundColor: '#1c2128',
    border: '1px solid #30363d',
    borderRadius: '12px',
    overflow: 'hidden',
    position: 'relative',
    minHeight: '600px',
  },
  iframe: {
    width: '100%',
    height: '100%',
    border: 'none',
    position: 'absolute',
    top: 0,
    left: 0,
  }
};
