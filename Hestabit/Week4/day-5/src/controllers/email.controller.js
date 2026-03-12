const { addEmailJob } = require('../jobs/email.job');
const logger = require('../utils/logger');

async function queueEmail(req, res) {
  const { email, subject, message, failOnce } = req.body;

  const job = await addEmailJob({
    email,
    subject,
    message,
    failOnce: Boolean(failOnce),
    requestId: req.requestId
  });

  logger.info({
    message: 'Email job queued',
    requestId: req.requestId,
    jobId: job.id,
    email
  });

  res.status(202).json({
    success: true,
    message: 'Email job queued successfully',
    requestId: req.requestId,
    jobId: job.id
  });
}

module.exports = {
  queueEmail
};
