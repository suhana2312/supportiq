import React, { useState, useEffect } from "react";
import { apiRequest } from "../../services/api";
import { Order, Refund, OrderStatus, RefundStatus } from "../../types";
import {
  ShoppingBag,
  Search,
  Filter,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  Eye,
  DollarSign,
  AlertCircle,
  Truck,
  Check,
  X,
  ChevronRight
} from "lucide-react";

export const AdminOrdersPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"orders" | "refunds">("orders");
  const [orders, setOrders] = useState<Order[]>([]);
  const [refunds, setRefunds] = useState<Refund[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [processingRefundId, setProcessingRefundId] = useState<string | null>(null);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      setError(null);
      const params: any = { page: 1, page_size: 50 };
      if (statusFilter !== "ALL") params.status = statusFilter;
      const res = await apiRequest<{ items: Order[]; total: number }>("/orders", { params });
      setOrders(res.items || []);
    } catch (err: any) {
      setError(err.message || "Failed to load orders");
    } finally {
      setLoading(false);
    }
  };

  const fetchRefunds = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiRequest<Refund[]>("/refunds");
      setRefunds(res || []);
    } catch (err: any) {
      setError(err.message || "Failed to load refunds");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "orders") {
      fetchOrders();
    } else {
      fetchRefunds();
    }
  }, [activeTab, statusFilter]);

  const handleUpdateRefundStatus = async (refundId: string, newStatus: RefundStatus) => {
    try {
      setProcessingRefundId(refundId);
      await apiRequest(`/refunds/${refundId}/status?status_update=${newStatus}`, {
        method: "PATCH",
      });
      await fetchRefunds();
    } catch (err: any) {
      alert(`Error updating refund: ${err.message}`);
    } finally {
      setProcessingRefundId(null);
    }
  };

  const filteredOrders = orders.filter((o) =>
    o.order_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
    o.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    o.customer_id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredRefunds = refunds.filter((r) =>
    r.order_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    r.customer_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    r.reason.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getStatusBadge = (status: OrderStatus) => {
    const config: Record<OrderStatus, { bg: string; text: string; icon: any }> = {
      DELIVERED: { bg: "bg-emerald-50 text-emerald-700 border-emerald-200", text: "Delivered", icon: CheckCircle },
      SHIPPED: { bg: "bg-blue-50 text-blue-700 border-blue-200", text: "Shipped", icon: Truck },
      OUT_FOR_DELIVERY: { bg: "bg-cyan-50 text-cyan-700 border-cyan-200", text: "Out for Delivery", icon: Truck },
      PROCESSING: { bg: "bg-amber-50 text-amber-700 border-amber-200", text: "Processing", icon: Clock },
      CONFIRMED: { bg: "bg-indigo-50 text-indigo-700 border-indigo-200", text: "Confirmed", icon: CheckCircle },
      PENDING: { bg: "bg-slate-50 text-slate-700 border-slate-200", text: "Pending", icon: Clock },
      CANCELLED: { bg: "bg-rose-50 text-rose-700 border-rose-200", text: "Cancelled", icon: XCircle },
    };
    const c = config[status] || config.PENDING;
    const Icon = c.icon;
    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${c.bg}`}>
        <Icon className="w-3.5 h-3.5" />
        {c.text}
      </span>
    );
  };

  const getRefundBadge = (status: RefundStatus) => {
    const map: Record<RefundStatus, string> = {
      REQUESTED: "bg-amber-100 text-amber-800 border-amber-300",
      APPROVED: "bg-emerald-100 text-emerald-800 border-emerald-300",
      REJECTED: "bg-rose-100 text-rose-800 border-rose-300",
      PROCESSING: "bg-blue-100 text-blue-800 border-blue-300",
      COMPLETED: "bg-purple-100 text-purple-800 border-purple-300",
    };
    return (
      <span className={`px-2.5 py-1 rounded-md text-xs font-semibold uppercase tracking-wider border ${map[status] || "bg-slate-100 text-slate-700"}`}>
        {status}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2.5">
            <ShoppingBag className="w-7 h-7 text-indigo-600" />
            Order & Refund Management
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Track customer orders, delivery states, and manage deterministic refund requests.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => (activeTab === "orders" ? fetchOrders() : fetchRefunds())}
            className="flex items-center gap-2 px-3.5 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200">
        <button
          onClick={() => setActiveTab("orders")}
          className={`px-5 py-3 text-sm font-semibold border-b-2 transition ${
            activeTab === "orders"
              ? "border-indigo-600 text-indigo-600"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          All Orders ({orders.length})
        </button>
        <button
          onClick={() => setActiveTab("refunds")}
          className={`px-5 py-3 text-sm font-semibold border-b-2 transition flex items-center gap-2 ${
            activeTab === "refunds"
              ? "border-indigo-600 text-indigo-600"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          Refund Requests ({refunds.length})
          {refunds.filter((r) => r.status === "REQUESTED").length > 0 && (
            <span className="bg-amber-500 text-white text-xs px-2 py-0.5 rounded-full font-bold">
              {refunds.filter((r) => r.status === "REQUESTED").length}
            </span>
          )}
        </button>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder={
              activeTab === "orders"
                ? "Search by Order #, Customer ID..."
                : "Search refunds by Order ID, Reason..."
            }
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
          />
        </div>
        {activeTab === "orders" && (
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            >
              <option value="ALL">All Statuses</option>
              <option value="DELIVERED">Delivered</option>
              <option value="SHIPPED">Shipped</option>
              <option value="OUT_FOR_DELIVERY">Out for Delivery</option>
              <option value="PROCESSING">Processing</option>
              <option value="CONFIRMED">Confirmed</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>
        )}
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg flex items-center gap-3 text-rose-700 text-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          {error}
        </div>
      )}

      {/* Tab Content: Orders Table */}
      {activeTab === "orders" && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3.5">Order #</th>
                  <th className="px-6 py-3.5">Customer ID</th>
                  <th className="px-6 py-3.5">Date Ordered</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5">Items</th>
                  <th className="px-6 py-3.5">Total Amount</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-slate-400">
                      <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-500" />
                      Loading orders...
                    </td>
                  </tr>
                ) : filteredOrders.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-slate-500">
                      No orders match your filter criteria.
                    </td>
                  </tr>
                ) : (
                  filteredOrders.map((order) => (
                    <tr key={order.id} className="hover:bg-slate-50/80 transition">
                      <td className="px-6 py-4 font-mono font-bold text-indigo-600">
                        #{order.order_number}
                      </td>
                      <td className="px-6 py-4 font-mono text-xs text-slate-600 truncate max-w-[140px]" title={order.customer_id}>
                        {order.customer_id}
                      </td>
                      <td className="px-6 py-4 text-slate-600 text-xs">
                        {new Date(order.ordered_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4">
                        {getStatusBadge(order.status)}
                      </td>
                      <td className="px-6 py-4 text-slate-600">
                        {order.items?.length || 0} item{(order.items?.length || 0) === 1 ? "" : "s"}
                      </td>
                      <td className="px-6 py-4 font-semibold text-slate-900">
                        ${order.total_amount.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => setSelectedOrder(order)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 rounded-md transition"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          View Details
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab Content: Refunds Table */}
      {activeTab === "refunds" && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3.5">Refund ID</th>
                  <th className="px-6 py-3.5">Order ID</th>
                  <th className="px-6 py-3.5">Amount</th>
                  <th className="px-6 py-3.5">Reason</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5">Date Filed</th>
                  <th className="px-6 py-3.5 text-right">Resolution Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-slate-400">
                      <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-500" />
                      Loading refunds...
                    </td>
                  </tr>
                ) : filteredRefunds.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-slate-500">
                      No refund requests found.
                    </td>
                  </tr>
                ) : (
                  filteredRefunds.map((refund) => (
                    <tr key={refund.id} className="hover:bg-slate-50/80 transition">
                      <td className="px-6 py-4 font-mono text-xs text-slate-600 truncate max-w-[120px]" title={refund.id}>
                        {refund.id.slice(0, 8)}...
                      </td>
                      <td className="px-6 py-4 font-mono text-xs text-indigo-600 truncate max-w-[120px]" title={refund.order_id}>
                        {refund.order_id.slice(0, 8)}...
                      </td>
                      <td className="px-6 py-4 font-bold text-slate-900">
                        ${refund.amount.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 text-xs text-slate-700 max-w-[200px] truncate" title={refund.reason}>
                        {refund.reason}
                      </td>
                      <td className="px-6 py-4">
                        {getRefundBadge(refund.status)}
                      </td>
                      <td className="px-6 py-4 text-xs text-slate-500">
                        {new Date(refund.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="inline-flex items-center gap-1.5 justify-end">
                          {refund.status === "REQUESTED" && (
                            <>
                              <button
                                disabled={processingRefundId === refund.id}
                                onClick={() => handleUpdateRefundStatus(refund.id, "APPROVED")}
                                className="px-2.5 py-1 text-xs font-semibold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 rounded-md transition flex items-center gap-1 disabled:opacity-50"
                              >
                                <Check className="w-3.5 h-3.5" /> Approve
                              </button>
                              <button
                                disabled={processingRefundId === refund.id}
                                onClick={() => handleUpdateRefundStatus(refund.id, "REJECTED")}
                                className="px-2.5 py-1 text-xs font-semibold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded-md transition flex items-center gap-1 disabled:opacity-50"
                              >
                                <X className="w-3.5 h-3.5" /> Reject
                              </button>
                            </>
                          )}
                          {refund.status === "APPROVED" && (
                            <button
                              disabled={processingRefundId === refund.id}
                              onClick={() => handleUpdateRefundStatus(refund.id, "COMPLETED")}
                              className="px-2.5 py-1 text-xs font-semibold text-purple-700 bg-purple-50 hover:bg-purple-100 border border-purple-200 rounded-md transition flex items-center gap-1 disabled:opacity-50"
                            >
                              <DollarSign className="w-3.5 h-3.5" /> Mark Paid
                            </button>
                          )}
                          {(refund.status === "COMPLETED" || refund.status === "REJECTED") && (
                            <span className="text-xs text-slate-400 font-medium italic">Archived</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Order Details Modal */}
      {selectedOrder && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl border border-slate-100 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div>
                <h3 className="text-lg font-bold text-slate-900">
                  Order Details: #{selectedOrder.order_number}
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Internal ID: {selectedOrder.id}
                </p>
              </div>
              <button
                onClick={() => setSelectedOrder(null)}
                className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="py-4 space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm bg-slate-50 p-4 rounded-xl">
                <div>
                  <span className="text-xs text-slate-400 block font-medium">Status</span>
                  <div className="mt-1">{getStatusBadge(selectedOrder.status)}</div>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block font-medium">Total Amount</span>
                  <span className="font-bold text-slate-900 text-base mt-1 block">
                    ${selectedOrder.total_amount.toFixed(2)} {selectedOrder.currency}
                  </span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block font-medium">Date Placed</span>
                  <span className="text-slate-700">
                    {new Date(selectedOrder.ordered_at).toLocaleString()}
                  </span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block font-medium">Delivered At</span>
                  <span className="text-slate-700">
                    {selectedOrder.delivered_at
                      ? new Date(selectedOrder.delivered_at).toLocaleString()
                      : "Not delivered yet"}
                  </span>
                </div>
                <div className="col-span-2">
                  <span className="text-xs text-slate-400 block font-medium">Shipping Address</span>
                  <span className="text-slate-700">{selectedOrder.shipping_address}</span>
                </div>
              </div>

              {/* Order Items */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
                  Line Items ({selectedOrder.items?.length || 0})
                </h4>
                <div className="border border-slate-200 rounded-lg divide-y divide-slate-100">
                  {selectedOrder.items && selectedOrder.items.length > 0 ? (
                    selectedOrder.items.map((item) => (
                      <div key={item.id} className="p-3 flex items-center justify-between text-sm">
                        <div>
                          <p className="font-medium text-slate-800">{item.product_name}</p>
                          <p className="text-xs text-slate-500">Qty: {item.quantity}</p>
                        </div>
                        <span className="font-semibold text-slate-900">
                          ${(item.price * item.quantity).toFixed(2)}
                        </span>
                      </div>
                    ))
                  ) : (
                    <div className="p-4 text-center text-xs text-slate-400">No line items recorded</div>
                  )}
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100 flex justify-end">
              <button
                onClick={() => setSelectedOrder(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium rounded-lg transition"
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
