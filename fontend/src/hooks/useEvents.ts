import { useState, useCallback } from 'react';
import { Event, ChatMessage, Snapshot, JudgeResult } from '../types/event';
import * as eventsApi from '../api/events';

interface UseEventsReturn {
  events: Event[];
  currentEvent: Event | null;
  isLoading: boolean;
  error: string | null;
  fetchEvents: () => Promise<void>;
  fetchEvent: (eventId: string) => Promise<void>;
  createEvent: (title: string, initialMessage: string) => Promise<Event>;
  sendPrivateChat: (eventId: string, message: string) => Promise<ChatMessage[]>;
  commitSnapshotA: (eventId: string, title: string, description: string) => Promise<Snapshot>;
  submitBAgreement: (eventId: string, agree: boolean, reason?: string) => Promise<void>;
  commitSnapshotB: (eventId: string, title: string, description: string) => Promise<Snapshot>;
  getJudgeResult: (eventId: string) => Promise<JudgeResult>;
  sendFollowupChat: (eventId: string, message: string) => Promise<ChatMessage[]>;
}

export const useEvents = (): UseEventsReturn => {
  const [events, setEvents] = useState<Event[]>([]);
  const [currentEvent, setCurrentEvent] = useState<Event | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 获取事件列表
  const fetchEvents = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await eventsApi.getEvents();
      setEvents(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch events');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 获取单个事件
  const fetchEvent = useCallback(async (eventId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await eventsApi.getEvent(eventId);
      setCurrentEvent(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch event');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 创建事件
  const createEvent = useCallback(async (title: string, initialMessage: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const event = await eventsApi.createEvent({ title, initialMessage });
      setEvents((prev) => [event, ...prev]);
      return event;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create event');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 发送私聊消息
  const sendPrivateChat = useCallback(async (eventId: string, message: string) => {
    setIsLoading(true);
    setError(null);
    try {
      return await eventsApi.sendPrivateChat(eventId, { message });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 提交快照A
  const commitSnapshotA = useCallback(async (eventId: string, title: string, description: string) => {
    setIsLoading(true);
    setError(null);
    try {
      return await eventsApi.commitSnapshotA(eventId, { title, description });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to commit snapshot A');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // B方同意/不同意
  const submitBAgreement = useCallback(async (eventId: string, agree: boolean, reason?: string) => {
    setIsLoading(true);
    setError(null);
    try {
      await eventsApi.submitBAgreement(eventId, { agree, reason });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit agreement');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 提交快照B
  const commitSnapshotB = useCallback(async (eventId: string, title: string, description: string) => {
    setIsLoading(true);
    setError(null);
    try {
      return await eventsApi.commitSnapshotB(eventId, { title, description });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to commit snapshot B');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 获取裁判结果
  const getJudgeResult = useCallback(async (eventId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      return await eventsApi.getJudgeResult(eventId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get judge result');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 发送复盘消息
  const sendFollowupChat = useCallback(async (eventId: string, message: string) => {
    setIsLoading(true);
    setError(null);
    try {
      return await eventsApi.sendFollowupChat(eventId, { message });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send followup message');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    events,
    currentEvent,
    isLoading,
    error,
    fetchEvents,
    fetchEvent,
    createEvent,
    sendPrivateChat,
    commitSnapshotA,
    submitBAgreement,
    commitSnapshotB,
    getJudgeResult,
    sendFollowupChat,
  };
};
