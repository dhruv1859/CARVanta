import { useState, useCallback } from 'react';
import html2canvas from 'html2canvas';
import '../styles/snapshot.css';

export default function SnapshotButton() {
    const [status, setStatus] = useState<'idle' | 'capturing' | 'done' | 'error'>('idle');
    const [savedPath, setSavedPath] = useState('');

    const takeSnapshot = useCallback(async () => {
        setStatus('capturing');

        try {
            // Brief delay for UI to show "capturing" state
            await new Promise(r => setTimeout(r, 100));

            // Capture the main content area (excluding the snapshot button itself)
            const target = document.querySelector('.main-content') as HTMLElement || document.body;

            const canvas = await html2canvas(target, {
                backgroundColor: '#0a0a1a',
                scale: 2,                   // High-res capture
                useCORS: true,
                logging: false,
                ignoreElements: (el) => el.classList.contains('snapshot-container'),
            });

            // Generate filename with page name and timestamp
            const pageName = document.title || 'CARVanta';
            const now = new Date();
            const timestamp = [
                now.getFullYear(),
                String(now.getMonth() + 1).padStart(2, '0'),
                String(now.getDate()).padStart(2, '0'),
                '_',
                String(now.getHours()).padStart(2, '0'),
                String(now.getMinutes()).padStart(2, '0'),
                String(now.getSeconds()).padStart(2, '0'),
            ].join('');

            const routeName = window.location.pathname.replace(/\//g, '-').replace(/^-/, '') || 'home';
            const filename = `CARVanta_${routeName}_${timestamp}.png`;

            // Trigger download
            const link = document.createElement('a');
            link.download = filename;
            link.href = canvas.toDataURL('image/png', 1.0);
            link.click();

            // Show saved path (browser downloads to Downloads folder)
            const downloadPath = `Downloads\\${filename}`;
            setSavedPath(downloadPath);
            setStatus('done');

            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                setStatus('idle');
                setSavedPath('');
            }, 5000);
        } catch (err) {
            console.error('Snapshot failed:', err);
            setStatus('error');
            setTimeout(() => setStatus('idle'), 3000);
        }
    }, []);

    return (
        <div className="snapshot-container">
            {/* Floating capture button */}
            <button
                className={`snapshot-btn ${status}`}
                onClick={takeSnapshot}
                disabled={status === 'capturing'}
                title="Take a snapshot of the current page"
            >
                {status === 'idle' && (
                    <>
                        <span className="snapshot-icon">📸</span>
                        <span className="snapshot-label">Snapshot</span>
                    </>
                )}
                {status === 'capturing' && (
                    <>
                        <span className="snapshot-icon spin">⏳</span>
                        <span className="snapshot-label">Capturing...</span>
                    </>
                )}
                {status === 'done' && (
                    <>
                        <span className="snapshot-icon">✅</span>
                        <span className="snapshot-label">Saved!</span>
                    </>
                )}
                {status === 'error' && (
                    <>
                        <span className="snapshot-icon">❌</span>
                        <span className="snapshot-label">Failed</span>
                    </>
                )}
            </button>

            {/* Toast notification showing save path */}
            {status === 'done' && savedPath && (
                <div className="snapshot-toast">
                    <div className="snapshot-toast-icon">📁</div>
                    <div className="snapshot-toast-content">
                        <div className="snapshot-toast-title">Snapshot Saved!</div>
                        <div className="snapshot-toast-path">{savedPath}</div>
                    </div>
                </div>
            )}
        </div>
    );
}
