// strata-mi50 (2026-10-27): the Record log button, one for the whole app, always in the same place (top centre) on every screen and
// chat, so a recording in progress is always visible (it was in the Monitor's header, 2026-10-26).  The recorder is
// lib/diagnostics-recorder.ts.
import { tr } from '../lib/i18n';
import { startRecording, stopRecording, useDiagnosticsRecording } from '../lib/diagnostics-recorder';
import { pushToast } from '../lib/store';

export function RecordLogButton() {
    const recorder = useDiagnosticsRecording();
    function toggle() {
        if (!recorder.recording) {
            startRecording();
            pushToast('success', tr('Recording the log'), tr('The Monitor readings are saved once a second, on every screen, until you press Stop.'));
            return;
        }
        try {
            const name = stopRecording();
            pushToast('success', tr('Log saved'), `${name} · ${tr('It is in your Downloads folder.')}`);
        }
        catch {
            pushToast('error', tr('The log was not saved'), tr('Try again.'));
        }
    }
    return <button type="button" className="record-log" data-on={recorder.recording} onClick={toggle}
        title={tr(recorder.recording ? 'Stop and save the log' : 'Record a log of every Monitor reading, once a second')}>
      <span className="record-log__dot" aria-hidden="true"/>
      <span>{tr(recorder.recording ? `Recording · ${recorder.count} s · Stop` : 'Record log')}</span>
    </button>;
}
