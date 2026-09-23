import React, { useState, useEffect } from "react";
import { apiRequest } from "../../services/api";
import { Order, RefundCheckResult } from "../../types";
import { Package, Truck, CheckCircle2, Clock, XCircle, AlertCircle, ShieldAlert, ArrowRight } from "lucide-react";

export const OrdersPage: React.FC = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [refundCheck, setRefundCheck] = useState<RefundCheckResult | null>(null);
  const [checkingRefund, setCheckingRefund] = useState(false);

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    try {
      const data = await apiRequest<{ items: Order[] }>("/orders", {
        params: { page: 1, page_size: 20 }
      });
      setOrders(data.items || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleCheckRefund = async (order: Order) => {
    setSelectedOrder(order);
    setCheckingRefund(true);
    setRefundCheck(null);
    try {
      const res = await apiRequest<RefundCheckResult>("/refunds/check-eligibility", {
        method: "POST",
        body: JSON.stringify({ order_number: order.order_number, reason: "Customer portal inquiry" })
      });
      setRefundCheck(res);
    } catch (err: any) {
      alert(err.message || "Failed to check refund eligibility");
    } finally {
      setCheckingRefund(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "DELIVERED":
        return <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1"><CheckCircle2 className="w-3.5 h-3.5" /> Delivered</span>;
      case "SHIPPED":
        return <span className="bg-blue-50 text-blue-700 border border-blue-200 px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1"><Truck className="w-3.5 h-3.5" /> In Transit</span>;
      case "CANCELLED":
        return <span className="bg-slate-100 text-slate-700 border border-slate-200 px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1"><XCircle className="w-3.5 h-3.5" /> Cancelled</span>;
      default:
        return <span className="bg-amber-50 text-amber-700 border border-amber-200 px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1"><Clock className="w-3.5 h-3.5" /> {status}</span>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">My Purchases & Orders</h1>
          <p className="text-sm text-slate-500">Track shipments, verify delivery receipts, and evaluate return eligibility.</p>
        </div>
      </div>

      {loading ? (
        <div className="p-8 text-center text-slate-400">Loading your purchases...</div>
      ) : orders.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-slate-200 max-w-md mx-auto">
          <Package className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="font-semibold text-slate-800">No Orders Placed Yet</h3>
          <p className="text-xs text-slate-500 mt-1">Orders you place will appear here with live tracking.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {orders.map((order) => (
            <div
              key={order.id}
              className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs hover:border-indigo-200 transition flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="space-y-2 flex-1">
                <div className="flex items-center gap-3">
                  <span className="font-bold text-base text-slate-900">Order #{order.order_number}</span>
                  {getStatusBadge(order.status)}
                  <span className="text-xs text-slate-400">
                    Ordered on {new Date(order.ordered_at).toLocaleDateString()}
                  </span>
                </div>

                <div className="text-xs text-slate-600">
                  <span className="font-semibold text-slate-700">Shipping to:</span> {order.shipping_address}
                </div>

                {order.items && order.items.length > 0 && (
                  <div className="flex flex-wrap gap-2 pt-1">
                    {order.items.map((item, idx) => (
                      <span
                        key={idx}
                        className="bg-slate-50 border border-slate-200 text-slate-700 text-xs px-2.5 py-1 rounded-md"
                      >
                        {item.quantity}x {item.product_name} (${item.price.toFixed(2)})
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex items-center gap-4 justify-between md:justify-end border-t md:border-t-0 pt-3 md:pt-0 border-slate-100">
                <div className="text-right">
                  <div className="text-xs text-slate-400 uppercase font-semibold">Total</div>
                  <div className="font-bold text-lg text-slate-900">
                    ${order.total_amount.toFixed(2)} {order.currency}
                  </div>
                </div>

                <button
                  onClick={() => handleCheckRefund(order)}
                  className="px-4 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 rounded-xl text-xs font-semibold transition"
                >
                  Refund Eligibility
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Refund Check Result Modal */}
      {selectedOrder && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="font-bold text-lg text-slate-900 mb-1">
              Refund Verification: Order #{selectedOrder.order_number}
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              Real-time evaluation against organization return policies and order history.
            </p>

            {checkingRefund ? (
              <div className="py-8 text-center text-slate-500 text-sm">
                Running deterministic business rules engine...
              </div>
            ) : refundCheck ? (
              <div className="space-y-4">
                <div
                  className={`p-4 rounded-xl border text-sm leading-relaxed ${
                    refundCheck.eligible
                      ? "bg-emerald-50 border-emerald-200 text-emerald-900"
                      : "bg-slate-50 border-slate-200 text-slate-800"
                  }`}
                >
                  <div className="flex items-center gap-2 font-bold mb-1">
                    {refundCheck.eligible ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                    ) : (
                      <AlertCircle className="w-5 h-5 text-amber-600" />
                    )}
                    {refundCheck.eligible ? "Eligible for Refund" : "Refund Request Notice"}
                  </div>
                  <p className="text-xs mt-1">{refundCheck.reason}</p>
                </div>

                <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-xs space-y-1">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Refundable Amount:</span>
                    <span className="font-bold text-slate-800">${refundCheck.refund_amount.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Manual Manager Approval:</span>
                    <span className="font-semibold text-slate-700">
                      {refundCheck.requires_manual_approval ? "Required" : "Automated Instant"}
                    </span>
                  </div>
                  {refundCheck.policy_citation && (
                    <div className="pt-2 border-t border-slate-200 text-[11px] text-indigo-700">
                      Policy Clause: <strong>{refundCheck.policy_citation}</strong>
                    </div>
                  )}
                </div>
              </div>
            ) : null}

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setSelectedOrder(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
