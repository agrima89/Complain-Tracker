/**
 * CampusCare - PDF Management Module
 * Generates official Grievance Ticket slips and Administrative Summary Reports
 * using pure JavaScript PDFKit (serverless-compatible, zero native dependencies).
 */

import PDFDocument from 'pdfkit';

const STATUS_LABELS = {
  NEW: 'Open',
  FORWARDED: 'Forwarded',
  IN_PROGRESS: 'In progress',
  REOPENED: 'Reopened',
  REGENERATED: 'Reopened',
  RESOLUTION_SUBMITTED: 'Awaiting confirmation',
  AWAITING_STUDENT_CONFIRMATION: 'Awaiting confirmation',
  FINAL_RESOLVED: 'Resolved'
};
const statusLabel = (s) => STATUS_LABELS[s] || String(s || 'NEW').replace(/_/g, ' ');

/**
 * Official complaint slip.
 * `photo` is optional: { data: Buffer, contentType } for the attached evidence. PDFKit can only
 * embed JPEG and PNG, so any other format is noted instead of drawn.
 */
export function generateComplaintPdfBuffer(complaint, history = [], photo = null, photoUrl = '') {
  return new Promise((resolve, reject) => {
    try {
      const M = 48;
      const doc = new PDFDocument({
        size: 'A4',
        margins: { top: M, bottom: M + 24, left: M, right: M },
        bufferPages: true,
        info: {
          Title: `Complaint ${complaint.ticket_id || complaint.complaint_id}`,
          Author: 'CampusCare',
          Subject: 'Complaint record'
        }
      });

      const buffers = [];
      doc.on('data', chunk => buffers.push(chunk));
      doc.on('end', () => resolve(Buffer.concat(buffers)));
      doc.on('error', err => reject(err));

      const INK = '#111827';
      const MUTED = '#6B7280';
      const LINE = '#E5E7EB';
      const ACCENT = '#D97706';
      const W = doc.page.width - M * 2;
      const bottom = () => doc.page.height - doc.page.margins.bottom;
      let y = M;

      // The slip is always a single page: sections shrink to fit instead of adding pages.
      const ensure = () => {};
      const heading = (text, keepWith = 40) => {
        ensure(26 + keepWith);
        doc.fillColor(MUTED).font('Helvetica-Bold').fontSize(8).text(text.toUpperCase(), M, y, { characterSpacing: 0.8 });
        y += 14;
        doc.moveTo(M, y).lineTo(M + W, y).lineWidth(0.6).strokeColor(LINE).stroke();
        y += 12;
      };

      // Header
      doc.roundedRect(M, y, 18, 18, 4).fill(ACCENT);
      doc.fillColor(INK).font('Helvetica-Bold').fontSize(12).text('CampusCare', M + 26, y + 3);
      doc.fillColor(MUTED).font('Helvetica').fontSize(9)
        .text('Student grievance portal', M, y + 5, { width: W, align: 'right' });
      y += 40;

      const ticketId = complaint.ticket_id || `CMP-${complaint.complaint_id}`;
      doc.fillColor(MUTED).font('Helvetica').fontSize(10).text(ticketId, M, y);
      y += 16;
      doc.fillColor(INK).font('Helvetica-Bold').fontSize(22).text(complaint.category || 'Complaint', M, y, { width: W - 150 });

      // Status chip, right aligned on the title line
      const status = statusLabel(complaint.status);
      doc.font('Helvetica-Bold').fontSize(9);
      const chipW = doc.widthOfString(status) + 20;
      doc.roundedRect(M + W - chipW, y + 4, chipW, 20, 10).fill(complaint.status === 'FINAL_RESOLVED' ? '#DCFCE7' : '#FEF3C7');
      doc.fillColor(complaint.status === 'FINAL_RESOLVED' ? '#166534' : '#92400E')
        .text(status, M + W - chipW, y + 10, { width: chipW, align: 'center' });
      y += 44;

      // Facts grid (4 columns)
      const isTransport = /transport/i.test(complaint.category || '');
      const location = isTransport
        ? [['Transport', complaint.transport_type || 'Bus'], ['Bus number', complaint.bus_number], ['Route', complaint.route], ['Stop', complaint.pickup_drop_point]]
        : [['Block', complaint.block || complaint.location], ['Floor', complaint.floor_no], ['Room', complaint.room_no], ['Side / nearby', complaint.corridor_side || complaint.nearby_area]];
      const facts = [
        ['Reported by', complaint.student_name || 'Registered student'],
        ['Email', complaint.student_email],
        ['Date reported', complaint.date],
        ...location,
        ['Priority', complaint.priority || 'Medium'],
        ['Department', complaint.department || complaint.category],
        ['Students affected', String(complaint.affected_student_count || 1)]
      ];
      heading('Details');
      const colW = W / 4;
      for (let i = 0; i < facts.length; i += 4) {
        const row = facts.slice(i, i + 4);
        doc.font('Helvetica').fontSize(10);
        const rowH = Math.max(...row.map(([, v]) => doc.heightOfString(String(v || '—'), { width: colW - 12 }))) + 16;
        ensure(rowH + 6);
        row.forEach(([k, v], j) => {
          const x = M + j * colW;
          doc.fillColor(MUTED).font('Helvetica').fontSize(8).text(k, x, y, { width: colW - 12 });
          doc.fillColor(INK).font('Helvetica').fontSize(10).text(String(v || '—'), x, y + 12, { width: colW - 12 });
        });
        y += rowH + 8;
      }
      y += 6;

      // Description
      heading('Description');
      doc.font('Helvetica').fontSize(10.5);
      const desc = complaint.description || 'No description provided.';
      const descH = Math.min(doc.heightOfString(desc, { width: W, lineGap: 3 }), 96); // ~6 lines max
      doc.fillColor(INK).text(desc, M, y, { width: W, lineGap: 3, height: descH, ellipsis: true });
      y += descH + 20;

      // Photo evidence (sized to leave room for the activity list, so the slip stays one page)
      heading('Photo evidence', 120);
      const embeddable = photo?.data && /image\/(jpe?g|png)/i.test(photo.contentType || '');
      let drew = false;
      if (embeddable) {
        try {
          const img = doc.openImage(photo.data);
          const maxH = Math.max(110, Math.min(240, bottom() - y - 150));
          const scale = Math.min(W / img.width, maxH / img.height, 1);
          const w = img.width * scale, h = img.height * scale;
          ensure(h + 10);
          doc.rect(M, y, w, h).lineWidth(0.6).strokeColor(LINE).stroke();
          doc.image(img, M, y, { width: w, height: h });
          y += h + 20;
          drew = true;
        } catch (e) {
          console.warn('[pdf] could not embed evidence photo:', e.message);
        }
      }
      if (!drew) {
        const note = !complaint.photo_path ? 'No photo was attached to this complaint.'
          : photo?.data ? 'A photo is attached in a format that can\'t be printed here. View it on the CampusCare portal.'
          : 'A photo is attached but couldn\'t be loaded. View it on the CampusCare portal.';
        doc.fillColor(MUTED).font('Helvetica').fontSize(10).text(note, M, y, { width: W });
        y = doc.y + 8;
      }
      if (drew) y -= 12;
      if (complaint.photo_path && photoUrl) {
        doc.fillColor(ACCENT).font('Helvetica-Bold').fontSize(9)
          .text('Open the photo online (sign-in required)', M, y, { width: W, link: photoUrl, underline: true, lineBreak: false });
        y += 14;
      }
      y += 12;

      // Activity
      if (history && history.length > 0) {
        heading('Activity');
        // Newest first; whatever doesn't fit on the page is summarised in one line.
        const items = history.slice().reverse();
        let shown = 0;
        for (const item of items) {
          const remark = item.remarks || (item.admin_name ? `By ${item.admin_name}` : '');
          const h = remark ? 34 : 20;
          if (y + h > bottom() - 14) break;
          doc.fillColor(MUTED).font('Helvetica').fontSize(9).text(String(item.changed_at || '').slice(0, 16), M, y, { width: 140, lineBreak: false });
          doc.fillColor(INK).font('Helvetica-Bold').fontSize(9.5).text(statusLabel(item.new_status), M + 150, y, { width: W - 150, lineBreak: false });
          if (remark) doc.fillColor(MUTED).font('Helvetica').fontSize(9).text(remark, M + 150, y + 14, { width: W - 150, height: 12, ellipsis: true });
          y += h;
          shown++;
        }
        if (shown < items.length) {
          doc.fillColor(MUTED).font('Helvetica').fontSize(9)
            .text(`+ ${items.length - shown} earlier update${items.length - shown === 1 ? '' : 's'}, see the portal for the full history.`, M, y, { width: W, lineBreak: false });
        }
      }

      // Footer on every page. Margins are lifted while drawing so the text doesn't trigger a new page.
      const generated = new Date().toISOString().slice(0, 16).replace('T', ' ') + ' UTC';
      const range = doc.bufferedPageRange();
      for (let i = range.start; i < range.start + range.count; i++) {
        doc.switchToPage(i);
        const saved = doc.page.margins.bottom;
        doc.page.margins.bottom = 0;
        const fy = doc.page.height - M;
        doc.moveTo(M, fy).lineTo(M + W, fy).lineWidth(0.6).strokeColor(LINE).stroke();
        doc.fillColor(MUTED).font('Helvetica').fontSize(8)
          .text(`CampusCare · ${ticketId} · Generated ${generated}`, M, fy + 8, { width: W - 60, lineBreak: false });
        doc.text(`Page ${i - range.start + 1} of ${range.count}`, M, fy + 8, { width: W, align: 'right', lineBreak: false });
        doc.page.margins.bottom = saved;
      }

      doc.end();
    } catch (err) {
      reject(err);
    }
  });
}

/**
 * Administrative summary report: headline counts, breakdowns and the most recent complaints.
 */
export function generateSummaryReportPdfBuffer({ stats, byCategory, byPriority, recent, scope }) {
  return new Promise((resolve, reject) => {
    try {
      const doc = new PDFDocument({ size: 'A4', margin: 40, info: { Title: 'CampusCare Summary Report', Author: 'CampusCare' } });
      const buffers = [];
      doc.on('data', c => buffers.push(c));
      doc.on('end', () => resolve(Buffer.concat(buffers)));
      doc.on('error', reject);

      const W = doc.page.width - 80;
      doc.rect(40, 40, W, 50).fill('#0F172A');
      doc.fillColor('#FFFFFF').font('Helvetica-Bold').fontSize(16).text('CampusCare — Complaint Summary Report', 55, 52);
      doc.fillColor('#94A3B8').font('Helvetica').fontSize(9)
        .text(`${scope || 'All departments'} · Generated ${new Date().toISOString().slice(0, 16).replace('T', ' ')} UTC`, 55, 72);

      let y = 110;
      const cards = [['Total', stats.total], ['Pending', stats.pending], ['In progress', stats.in_progress], ['Resolved', stats.resolved]];
      const cw = W / cards.length;
      cards.forEach(([label, val], i) => {
        const x = 40 + i * cw;
        doc.rect(x + 2, y, cw - 4, 54).fillAndStroke('#F8FAFC', '#CBD5E1');
        doc.fillColor('#64748B').font('Helvetica-Bold').fontSize(8).text(label.toUpperCase(), x + 12, y + 10);
        doc.fillColor('#0F172A').fontSize(20).text(String(val ?? 0), x + 12, y + 24);
      });
      y += 74;
      const rate = stats.total ? ((stats.resolved / stats.total) * 100).toFixed(1) : '0.0';
      doc.fillColor('#0F172A').font('Helvetica').fontSize(10).text(`Resolution rate: ${rate}%`, 40, y);
      y += 24;

      const section = (title, rows) => {
        doc.fillColor('#0284C7').font('Helvetica-Bold').fontSize(11).text(title, 40, y); y += 18;
        if (!rows.length) { doc.fillColor('#64748B').font('Helvetica').fontSize(9).text('No data', 40, y); y += 16; }
        rows.forEach(([k, v]) => {
          doc.fillColor('#0F172A').font('Helvetica').fontSize(9).text(k, 50, y, { width: 300 });
          doc.text(String(v), 360, y, { width: 80, align: 'right' }); y += 14;
        });
        y += 10;
      };
      section('By category', byCategory.map(r => [r.category || 'Other', r.count]));
      section('By priority', byPriority.map(r => [r.priority || 'Medium', r.count]));

      doc.fillColor('#0284C7').font('Helvetica-Bold').fontSize(11).text('Most recent complaints', 40, y); y += 18;
      const cols = [['Ticket', 40, 90], ['Category', 130, 110], ['Priority', 240, 55], ['Status', 295, 90], ['Date', 385, 70], ['Location', 455, 100]];
      const header = () => {
        doc.fillColor('#64748B').font('Helvetica-Bold').fontSize(8);
        cols.forEach(([h, x, w]) => doc.text(h, x, y, { width: w })); y += 14;
      };
      header();
      recent.forEach(c => {
        if (y > doc.page.height - 60) { doc.addPage(); y = 40; header(); }
        const vals = [c.ticket_id, c.category, c.priority, c.status, String(c.date || '').slice(0, 10), c.block || c.location || ''];
        doc.fillColor('#0F172A').font('Helvetica').fontSize(8);
        cols.forEach(([, x, w], i) => doc.text(String(vals[i] ?? ''), x, y, { width: w, height: 11, ellipsis: true }));
        y += 13;
      });
      doc.end();
    } catch (e) { reject(e); }
  });
}
