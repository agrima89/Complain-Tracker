/**
 * CampusCare - PDF Management Module
 * Generates official Grievance Ticket slips and Administrative Summary Reports
 * using pure JavaScript PDFKit (serverless-compatible, zero native dependencies).
 */

import PDFDocument from 'pdfkit';

export function generateComplaintPdfBuffer(complaint, history = []) {
  return new Promise((resolve, reject) => {
    try {
      const doc = new PDFDocument({
        size: 'A4',
        margin: 40,
        info: {
          Title: `Grievance Report - ${complaint.ticket_id || complaint.complaint_id}`,
          Author: 'CampusCare Grievance Redressal System',
          Subject: 'Official Complaint Record'
        }
      });

      const buffers = [];
      doc.on('data', chunk => buffers.push(chunk));
      doc.on('end', () => resolve(Buffer.concat(buffers)));
      doc.on('error', err => reject(err));

      const primaryNavy = '#0F172A';
      const accentSky = '#0284C7';
      const textMuted = '#64748B';
      const cardBg = '#F8FAFC';
      const borderColor = '#CBD5E1';

      // 1. Header Banner
      doc.rect(40, 40, doc.page.width - 80, 50).fill(primaryNavy);
      doc.fillColor('#FFFFFF').fontSize(16).font('Helvetica-Bold')
        .text('CampusCare — Student Grievance Portal', 55, 52);
      doc.fillColor('#94A3B8').fontSize(9).font('Helvetica')
        .text('Institutional Grievance Redressal & Resolution Tracking System', 55, 72);

      // 2. Ticket Badge Box
      let y = 105;
      const ticketId = complaint.ticket_id || `CMP-${complaint.complaint_id}`;
      doc.rect(40, y, doc.page.width - 80, 40).fillAndStroke('#F0F9FF', '#BAE6FD');
      doc.fillColor(accentSky).fontSize(10).font('Helvetica-Bold')
        .text('TICKET REFERENCE:', 55, y + 14);
      doc.fillColor(primaryNavy).fontSize(14).font('Helvetica-Bold')
        .text(ticketId, 190, y + 12);

      // Status Pill
      const status = (complaint.status || 'NEW').replace(/_/g, ' ');
      doc.rect(doc.page.width - 180, y + 8, 125, 24).fillAndStroke('#E0F2FE', '#7DD3FC');
      doc.fillColor(accentSky).fontSize(9).font('Helvetica-Bold')
        .text(status.toUpperCase(), doc.page.width - 180, y + 16, { width: 125, align: 'center' });

      y += 55;

      // 3. Metadata Table Grid
      doc.rect(40, y, doc.page.width - 80, 110).fillAndStroke(cardBg, borderColor);

      doc.fillColor(textMuted).fontSize(8).font('Helvetica-Bold');
      doc.text('STUDENT NAME', 55, y + 12);
      doc.text('EMAIL ADDRESS', 220, y + 12);
      doc.text('DATE LODGED', 400, y + 12);

      doc.fillColor(primaryNavy).fontSize(10).font('Helvetica');
      doc.text(complaint.student_name || 'Registered Student', 55, y + 24);
      doc.text(complaint.student_email || '—', 220, y + 24);
      doc.text(complaint.date || '—', 400, y + 24);

      // Second row of metadata
      doc.fillColor(textMuted).fontSize(8).font('Helvetica-Bold');
      doc.text('CATEGORY', 55, y + 55);
      doc.text('PRIORITY LEVEL', 220, y + 55);
      doc.text('AFFECTED STUDENTS', 400, y + 55);

      doc.fillColor(primaryNavy).fontSize(10).font('Helvetica');
      doc.text(complaint.category || 'General', 55, y + 67);
      doc.text(complaint.priority || 'Medium', 220, y + 67);
      doc.text(`${complaint.affected_student_count || 1} Student(s) Reported`, 400, y + 67);

      y += 125;

      // 4. Location Details
      doc.rect(40, y, doc.page.width - 80, 65).fillAndStroke(cardBg, borderColor);
      doc.fillColor(accentSky).fontSize(10).font('Helvetica-Bold')
        .text('CAMPUS LOCATION & AREA DETAILS', 55, y + 10);

      let locationText = '';
      if (complaint.category === 'Transport Complaint') {
        locationText = `Transport Mode: ${complaint.transport_type || 'Bus'} | Bus No: ${complaint.bus_number || '—'} | Route: ${complaint.route || '—'} | Stop: ${complaint.pickup_drop_point || '—'}`;
      } else {
        const parts = [];
        if (complaint.block) parts.push(`Block: ${complaint.block}`);
        if (complaint.floor_no) parts.push(`Floor: ${complaint.floor_no}`);
        if (complaint.room_no) parts.push(`Room: ${complaint.room_no}`);
        if (complaint.corridor_side) parts.push(`Side: ${complaint.corridor_side}`);
        if (complaint.nearby_area) parts.push(`Landmark: ${complaint.nearby_area}`);
        locationText = parts.length > 0 ? parts.join(' • ') : (complaint.location || 'Campus Premises');
      }

      doc.fillColor(primaryNavy).fontSize(9).font('Helvetica')
        .text(locationText, 55, y + 28, { width: doc.page.width - 110 });

      y += 80;

      // 5. Issue Description
      doc.rect(40, y, doc.page.width - 80, 140).fillAndStroke(cardBg, borderColor);
      doc.fillColor(accentSky).fontSize(10).font('Helvetica-Bold')
        .text('GRIEVANCE DESCRIPTION', 55, y + 10);

      doc.fillColor(primaryNavy).fontSize(9).font('Helvetica')
        .text(complaint.description || 'No description provided.', 55, y + 28, {
          width: doc.page.width - 110,
          height: 100,
          ellipsis: true
        });

      y += 155;

      // 6. Photo Evidence & Verification Note
      doc.rect(40, y, doc.page.width - 80, 45).fillAndStroke('#F8FAFC', '#E2E8F0');
      doc.fillColor(primaryNavy).fontSize(9).font('Helvetica-Bold')
        .text('📸 PHOTO EVIDENCE STATUS:', 55, y + 14);

      const hasPhoto = Boolean(complaint.photo_path);
      const photoStatus = hasPhoto
        ? 'Verified digital photo evidence attached & encrypted in registry.'
        : 'No photo evidence on record.';
      doc.fillColor(hasPhoto ? '#059669' : textMuted).fontSize(9).font('Helvetica')
        .text(photoStatus, 215, y + 14);

      y += 60;

      // 7. Audit Status History if present
      if (history && history.length > 0) {
        doc.fillColor(accentSky).fontSize(10).font('Helvetica-Bold')
          .text('LIFECYCLE STATUS AUDIT TRAIL', 40, y);
        y += 16;

        for (const item of history.slice(0, 4)) {
          doc.rect(40, y, doc.page.width - 80, 24).fillAndStroke('#FFFFFF', '#E2E8F0');
          doc.fillColor(textMuted).fontSize(8).font('Helvetica')
            .text(item.changed_at || '', 50, y + 7);
          doc.fillColor(primaryNavy).fontSize(8).font('Helvetica-Bold')
            .text(`${item.old_status ? item.old_status + ' → ' : ''}${item.new_status}`, 160, y + 7);
          doc.fillColor(textMuted).fontSize(8).font('Helvetica')
            .text(item.remarks || item.admin_name || 'Status updated', 300, y + 7, { width: 220, ellipsis: true });
          y += 28;
        }
      }

      // 8. Footer
      const footerY = doc.page.height - 50;
      doc.moveTo(40, footerY).lineTo(doc.page.width - 40, footerY).stroke(borderColor);
      doc.fillColor(textMuted).fontSize(7).font('Helvetica')
        .text('Generated by CampusCare Grievance Redressal System  |  Valid university administrative slip without physical signature.', 40, footerY + 8);
      doc.text(`Generated: ${new Date().toLocaleString()}`, doc.page.width - 180, footerY + 8, { width: 140, align: 'right' });

      doc.end();
    } catch (err) {
      reject(err);
    }
  });
}
