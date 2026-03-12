const { Queue, Worker } = require('bullmq');
const IORedis = require('ioredis');
const logger = require('../utils/logger');

const connection = new IORedis({
  host: process.env.REDIS_HOST || '127.0.0.1',
  port: Number(process.env.REDIS_PORT) || 6379,
  maxRetriesPerRequest: null
});

const emailQueue = new Queue('emailQueue', { connection });

async function addEmailJob(payload) {
  return emailQueue.add('sendEmail', payload, {
    attempts: 3,
    backoff: {
      type: 'exponential',
      delay: 2000
    },
    removeOnComplete: 50,
    removeOnFail: 20
  });
}

const worker = new Worker(
  'emailQueue',
  async (job) => {
    logger.info({
      message: 'Processing email job',
      jobId: job.id,
      requestId: job.data.requestId,
      email: job.data.email,
      subject: job.data.subject
    });

    await new Promise((resolve) => setTimeout(resolve, 1000));

    if (job.data.failOnce && job.attemptsMade === 0) {
      throw new Error('Simulated email failure for retry test');
    }

    logger.info({
      message: 'Email job completed',
      jobId: job.id,
      requestId: job.data.requestId,
      email: job.data.email
    });

    return { success: true };
  },
  { connection }
);

worker.on('completed', (job) => {
  logger.info({
    message: 'Worker completed job',
    jobId: job.id
  });
});

worker.on('failed', (job, err) => {
  logger.error({
    message: 'Worker failed job',
    jobId: job?.id,
    error: err.message
  });
});

module.exports = {
  addEmailJob,
  emailQueue
};
