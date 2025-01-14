import { z } from "zod";
import { createTRPCRouter, protectedProcedure } from "../trpc";
import { TRPCError } from "@trpc/server";
import { db } from "~/server/db";
import { CallService } from "@repo/services/src/call";
import {
  BlockChangeSchema,
  FilterSchema,
  OrderBySchema,
} from "@repo/types/src/index";

const callService = new CallService(db);

export const callRouter = createTRPCRouter({
  getCall: protectedProcedure
    .input(z.string())
    .query(async ({ input, ctx }) => {
      const call = await callService.getCall(input, ctx.orgId);
      if (!call) {
        throw new TRPCError({
          code: "NOT_FOUND",
          message: "Call not found",
        });
      }
      return call;
    }),

  getCalls: protectedProcedure
    .input(
      z.object({
        testId: z.string().optional(),
        scenarioId: z.string().optional(),
        limit: z.number().optional(),
        cursor: z.string().optional(),
        filter: FilterSchema.partial(),
        orderBy: OrderBySchema.optional(),
      }),
    )
    .query(async ({ input, ctx }) => {
      const limit = input.limit ?? 50;
      const result = await callService.getCalls({
        ...input,
        ownerId: ctx.orgId,
        limit,
      });

      return {
        calls: result.items,
        nextCursor: result.nextCursor,
      };
    }),

  getCallsByCustomerCallId: protectedProcedure
    .input(z.object({ customerCallId: z.string() }))
    .query(async ({ input, ctx }) => {
      return await callService.getCallsByCustomerCallId({
        customerCallId: input.customerCallId,
        orgId: ctx.orgId,
      });
    }),

  updateIsRead: protectedProcedure
    .input(z.object({ callId: z.string(), isRead: z.boolean() }))
    .mutation(async ({ input, ctx }) => {
      return await callService.updateIsRead({
        callId: input.callId,
        orgId: ctx.orgId,
        userId: ctx.userId,
        isRead: input.isRead,
      });
    }),

  updateNotes: protectedProcedure
    .input(z.object({ callId: z.string(), notes: z.string() }))
    .mutation(async ({ input, ctx }) => {
      return await callService.updateNotes({
        callId: input.callId,
        orgId: ctx.orgId,
        notes: input.notes,
      });
    }),

  checkIfACallExists: protectedProcedure.query(async ({ ctx }) => {
    return await callService.checkIfACallExists(ctx.orgId);
  }),

  getLatencyInterruptionPercentiles: protectedProcedure
    .input(z.object({ filter: FilterSchema.partial() }))
    .query(async ({ input, ctx }) => {
      return await callService.getLatencyInterruptionPercentiles({
        filter: input.filter,
        ownerId: ctx.orgId,
      });
    }),

  updateBlocks: protectedProcedure
    .input(z.object({ callId: z.string(), blocks: z.array(BlockChangeSchema) }))
    .mutation(async ({ input, ctx }) => {
      return await callService.updateBlocks({
        callId: input.callId,
        blocks: input.blocks,
        ownerId: ctx.orgId,
      });
    }),

  getAgentIds: protectedProcedure.query(async ({ ctx }) => {
    return await callService.getAgentIds(ctx.orgId);
  }),

  getMetadata: protectedProcedure.query(async ({ ctx }) => {
    return await callService.getMetadata(ctx.orgId);
  }),
});
