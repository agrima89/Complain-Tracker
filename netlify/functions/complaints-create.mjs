import { query, initDb } from './utils/db.mjs';
import { getSessionFromEvent } from './utils/auth.mjs';
import {
  computeComplaintFingerprint,
  formatTicketId,
  extractCanonicalRoom
} from './utils/duplicate_logic.mjs';

const VALID_CATEGORIES = [
  "Electrical", "Cleaning", "Hostel", "Wi-Fi/Internet", "Classroom",
  "Library", "Infrastructure", "Transport Complaint", "Other",
  "Academic", "Plumbing & Water Supply", "Cleanliness & Hygiene",
  "Infrastructure & Maintenance", "Mess/Canteen", "Security", "IT & Internet"
];

const VALID_BLOCKS = [
  "Block A", "Block B", "Block C", "Block D", "Block E", "Block F",
  "Academic Block", "Hostel", "Library", "Campus", "Sports", "Other"
];

const CATEGORY_DEPT_MAP = {
  "Electrical": "Electrical",
  "Cleaning": "Cleaning",
  "Classroom": "Classroom",
  "Hostel": "Hostel",
  "Wi-Fi/Internet": "Wi-Fi/Internet",
  "IT & Internet": "Wi-Fi/Internet",
  "Library": "Library",
  "Infrastructure": "Infrastructure",
  "Infrastructure & Maintenance": "Infrastructure",
  "Plumbing & Water Supply": "Cleaning",
  "Cleanliness & Hygiene": "Cleaning",
  "Academic": "Classroom",
  "Mess/Canteen": "Hostel",
  "Security": "Other",
  "Transport Complaint": "Transport",
  "Other": "Other"
};

export const handler = async (event, context) => {
  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Method Not Allowed' })
    };
  }

  const session = getSessionFromEvent(event);
  if (!session.authenticated || !session.user.student_id) {
    return {
      statusCode: 401,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Unauthorized: Student authentication required.' })
    };
  }

  const studentId = session.user.student_id;
  const studentEmail = session.user.student_email || '';

  try {
    await initDb();
    let body = {};
    try {
      body = JSON.parse(event.body || '{}');
    } catch {
      return {
        statusCode: 400,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: false, error: 'Invalid JSON request body' })
      };
    }

    const category = (body.category || '').trim();
    const description = (body.description || '').trim();
    const photoPath = (body.photo_path || body.photoPath || (body.photo_data ? 'evidence/photo.jpg' : '')).trim();
    const priority = (body.priority || 'Medium').trim();

    // Campus location fields
    const block = (body.block || '').trim();
    const floorNo = (body.floor_no || '').trim();
    const roomNo = (body.room_no || '').trim();
    const corridorSide = (body.corridor_side || '').trim();
    const nearbyArea = (body.nearby_area || '').trim();
    const additionalLocation = (body.additional_location || '').trim();

    // Transport fields
    const transportType = (body.transport_type || '').trim();
    const busNumber = (body.bus_number || '').trim();
    const route = (body.route || '').trim();
    const pickupDropPoint = (body.pickup_drop_point || '').trim();
    const transportComplaintType = (body.transport_complaint_type || '').trim();

    // 1. Validation
    if (!category || !VALID_CATEGORIES.includes(category)) {
      return {
        statusCode: 400,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: false, error: 'Please select a valid complaint category.' })
      };
    }

    if (!description || description.length < 5 || description.length > 2000) {
      return {
        statusCode: 400,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: false, error: 'Please provide a detailed description (5 to 2000 characters).' })
      };
    }

    if (!photoPath) {
      return {
        statusCode: 400,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: false, error: 'Photo evidence is required to submit this complaint.' })
      };
    }

    if (category === 'Transport Complaint') {
      if (!busNumber || !route || !pickupDropPoint || !transportComplaintType) {
        return {
          statusCode: 400,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            success: false,
            error: 'Bus Number, Route, Pickup/Drop Point, and Complaint Type are required for Transport Complaints.'
          })
        };
      }
    } else {
      if (!block || !VALID_BLOCKS.includes(block)) {
        return {
          statusCode: 400,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ success: false, error: 'Please select the campus location/block where the issue is located.' })
        };
      }
    }

    // Room/Floor consistency validation
    if (roomNo && floorNo) {
      const canonRoom = extractCanonicalRoom(roomNo);
      if (canonRoom && /^[0-9]/.test(canonRoom)) {
        let impliedFloor = null;
        const firstDigit = canonRoom[0];
        if (firstDigit === '0') impliedFloor = 'ground';
        else if (firstDigit === '1') impliedFloor = '1st';
        else if (firstDigit === '2') impliedFloor = '2nd';
        else if (firstDigit === '3') impliedFloor = '3rd';
        else if (firstDigit === '4') impliedFloor = '4th';
        else if (firstDigit === '5') impliedFloor = '5th';

        if (impliedFloor && !floorNo.toLowerCase().includes(impliedFloor)) {
          return {
            statusCode: 400,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              success: false,
              status: 'VALIDATION_FAILED',
              error: `Inconsistent location: Room ${roomNo} appears to be on the ${impliedFloor} floor, but you selected '${floorNo}'. Please correct the location.`
            })
          };
        }
      }
    }

    // Compose formatted display location
    let rawLocation = '';
    if (category === 'Transport Complaint') {
      rawLocation = `Bus ${busNumber} • Route ${route} • ${pickupDropPoint}`;
    } else {
      const locParts = [block];
      if (floorNo) locParts.push(floorNo);
      if (roomNo) locParts.push(`Room ${roomNo}`);
      if (corridorSide) locParts.push(`(${corridorSide})`);
      if (nearbyArea) locParts.push(`near ${nearbyArea}`);
      rawLocation = locParts.join(', ');
    }

    const todayDate = new Date().toISOString().slice(0, 10);
    const nowTimestamp = new Date().toISOString().replace('T', ' ').slice(0, 19);

    // Compute deterministic fingerprint
    const fingerprint = computeComplaintFingerprint({
      category,
      description,
      block,
      floor_no: floorNo,
      room_no: roomNo,
      corridor_side: corridorSide,
      nearby_area: nearbyArea,
      additional_location: additionalLocation,
      location: rawLocation,
      transport_type: transportType,
      bus_number: busNumber,
      route,
      pickup_drop_point: pickupDropPoint,
      transport_complaint_type: transportComplaintType
    });

    // Check for existing active master complaint
    const masterRes = await query(`
      SELECT * FROM complaints
      WHERE complaint_fingerprint = $1
        AND status != 'FINAL_RESOLVED'
      ORDER BY complaint_id DESC LIMIT 1
    `, [fingerprint]);

    const master = masterRes.rows[0];

    if (master) {
      const masterId = master.complaint_id;
      const masterTicket = master.ticket_id || formatTicketId(masterId, master.date);

      // Check if student is already in complaint_reporters
      const repCheck = await query(`
        SELECT 1 FROM complaint_reporters
        WHERE complaint_id = $1 AND student_id = $2
      `, [masterId, studentId]);

      if (repCheck.rows.length > 0) {
        // Reject duplicate
        const dupMsg = `Duplicate Complaint Detected: You have already submitted an active complaint (${masterTicket}) for this issue at this location. Please track your existing complaint instead of submitting the same issue again.`;
        return {
          statusCode: 409,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            success: false,
            status: 'DUPLICATE_REJECTED',
            error: dupMsg,
            message: dupMsg,
            complaint_id: masterId,
            ticket_id: masterTicket,
            affected_student_count: master.affected_student_count || 1,
            current_status: master.status,
            category: master.category,
            location: master.location
          })
        };
      } else {
        // Attach to master as non-primary
        const department = master.department || CATEGORY_DEPT_MAP[category] || 'Other';
        const insertRes = await query(`
          INSERT INTO complaints (
            student_id, category, description, photo_path, block, floor_no, room_no,
            corridor_side, nearby_area, additional_location, priority,
            transport_type, bus_number, route, pickup_drop_point, transport_complaint_type,
            department, status, date, location, complaint_fingerprint,
            affected_student_count, is_primary, group_id, regeneration_count, last_updated
          ) VALUES (
            $1, $2, $3, $4, $5, $6, $7,
            $8, $9, $10, $11,
            $12, $13, $14, $15, $16,
            $17, 'NEW', $18, $19, $20,
            1, FALSE, $21, 0, $22
          ) RETURNING complaint_id
        `, [
          studentId, category, description, photoPath, block, floorNo, roomNo,
          corridorSide, nearbyArea, additionalLocation, priority,
          transportType, busNumber, route, pickupDropPoint, transportComplaintType,
          department, todayDate, master.location || rawLocation, fingerprint,
          masterId, nowTimestamp
        ]);

        const newComplaintId = insertRes.lastRowId || insertRes.rows[0]?.complaint_id;
        const newTicketId = formatTicketId(newComplaintId, todayDate);

        await query(`UPDATE complaints SET ticket_id = $1 WHERE complaint_id = $2`, [newTicketId, newComplaintId]);

        // Insert into complaint_reporters for master and new
        await query(`
          INSERT INTO complaint_reporters (complaint_id, student_id, student_email, reported_at)
          VALUES ($1, $2, $3, $4)
        `, [masterId, studentId, studentEmail, nowTimestamp]);

        await query(`
          INSERT INTO complaint_reporters (complaint_id, student_id, student_email, reported_at)
          VALUES ($1, $2, $3, $4)
        `, [newComplaintId, studentId, studentEmail, nowTimestamp]);

        // Increment affected_student_count on master
        await query(`
          UPDATE complaints
          SET affected_student_count = affected_student_count + 1
          WHERE complaint_id = $1
        `, [masterId]);

        const newCount = (master.affected_student_count || 1) + 1;

        const attachObj = {
          success: true,
          status: 'ATTACHED_TO_MASTER',
          complaint_id: newComplaintId,
          ticket_id: newTicketId,
          master_id: masterId,
          master_ticket: masterTicket,
          affected_student_count: newCount,
          current_status: master.status,
          category,
          location: rawLocation,
          is_grouped: true,
          submitted_date: todayDate,
          message: `Your complaint has been registered. You have been grouped with an existing active issue. Your Ticket ID is ${newTicketId}.`
        };

        return {
          statusCode: 201,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ...attachObj,
            data: attachObj
          })
        };
      }
    }

    // No master exists: Create new master complaint
    const department = CATEGORY_DEPT_MAP[category] || 'Other';
    const insertRes = await query(`
      INSERT INTO complaints (
        student_id, ticket_id, category, description, photo_path, block, floor_no, room_no,
        corridor_side, nearby_area, additional_location, location, priority, status, date, last_updated,
        transport_type, bus_number, route, pickup_drop_point, transport_complaint_type, department,
        complaint_fingerprint, affected_student_count, group_id, is_primary
      ) VALUES (
        $1, '', $2, $3, $4, $5, $6, $7,
        $8, $9, $10, $11, $12, 'NEW', $13, $14,
        $15, $16, $17, $18, $19, $20,
        $21, 1, NULL, TRUE
      ) RETURNING complaint_id
    `, [
      studentId, category, description, photoPath, block, floorNo, roomNo,
      corridorSide, nearbyArea, additionalLocation, rawLocation, priority, todayDate, nowTimestamp,
      transportType, busNumber, route, pickupDropPoint, transportComplaintType, department,
      fingerprint
    ]);

    const complaintId = insertRes.lastRowId || insertRes.rows[0]?.complaint_id;
    const ticketId = formatTicketId(complaintId, todayDate);

    await query(`
      UPDATE complaints SET ticket_id = $1, group_id = $2 WHERE complaint_id = $3
    `, [ticketId, complaintId, complaintId]);

    await query(`
      INSERT INTO complaint_reporters (complaint_id, student_id, student_email, reported_at)
      VALUES ($1, $2, $3, $4)
    `, [complaintId, studentId, studentEmail, nowTimestamp]);

    await query(`
      INSERT INTO complaint_status_history (
        complaint_id, admin_id, admin_name, old_status, new_status, remarks, changed_at
      ) VALUES (
        $1, NULL, 'Student (Submission)', NULL, 'NEW', 'Grievance ticket created and lodged for administration review.', $2
      )
    `, [complaintId, nowTimestamp]);

    const slotKey = `${studentId}::${fingerprint}`;
    await query(`
      INSERT INTO active_complaint_slots (slot_key, complaint_id, student_id, created_at)
      VALUES ($1, $2, $3, $4)
    `, [slotKey, complaintId, studentId, nowTimestamp]);

    const finalObj = {
      success: true,
      status: 'CREATED_NEW',
      complaint_id: complaintId,
      ticket_id: ticketId,
      affected_student_count: 1,
      is_grouped: false,
      submitted_date: todayDate,
      message: `Grievance ticket ${ticketId} submitted successfully.`
    };

    return {
      statusCode: 201,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...finalObj,
        data: finalObj
      })
    };
  } catch (err) {
    console.error('[complaints-create] Error:', err);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Database error processing complaint submission.' })
    };
  }
};
